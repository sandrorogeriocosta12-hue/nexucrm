# cython: language_level=3, boundscheck=False, wraparound=False
# weight_adjustment.pyx
# 
# Wrapper Cython para o módulo de aprendizado automático em C
#

"""
Cython wrapper para weight_adjustment.c

Este módulo fornece uma interface Python para o motor de aprendizado
automático de pesos fuzzy do Nexus Service.
"""

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from libc.string cimport memset, strcpy
from cpython.ref cimport PyObject

cdef extern from "weight_adjustment.h":
    ctypedef struct LeadFeatures:
        double engagement
        double intention
        double ai_confidence
        char niche[64]
        long timestamp
    
    ctypedef struct PredictionResult:
        double predicted_score
        double closure_probability
        double rule_activations[12]
    
    ctypedef struct SalesOutcome:
        double actual_outcome
        int was_converted
        char feedback_text[256]
        long feedback_timestamp
    
    ctypedef struct FuzzyWeights:
        double weights[12]
        double biases[3]
        double learning_rate
        long updates_count
        double total_train_error
    
    ctypedef struct LearningContext:
        FuzzyWeights weights
        PredictionResult *predictions_history
        SalesOutcome *outcomes_history
        int history_size
        int history_capacity
        double accuracy
        double precision
        double recall
        double f1_score
    
    # Inicialização
    LearningContext* learning_context_init(int history_capacity)
    void learning_context_free(LearningContext *ctx)
    
    # Fuzzificação
    double fuzzify_engagement_low(double e)
    double fuzzify_engagement_medium(double e)
    double fuzzify_engagement_high(double e)
    
    double fuzzify_intention_low(double i)
    double fuzzify_intention_medium(double i)
    double fuzzify_intention_high(double i)
    
    double fuzzify_confidence_low(double u)
    double fuzzify_confidence_medium(double u)
    double fuzzify_confidence_high(double u)
    
    # Inferência
    void apply_fuzzy_rules(LeadFeatures *features, FuzzyWeights *weights,
                           PredictionResult *result)
    double defuzzify_centroid(double *activations, int num_rules)
    double calculate_closure_probability(double lead_score, const char *niche_memory)
    
    # Predição
    PredictionResult* predict_lead(LeadFeatures *features, FuzzyWeights *weights)
    
    # Aprendizado
    double calculate_error(double actual_outcome, double predicted_score)
    void update_weights(FuzzyWeights *weights, double error,
                        PredictionResult *activations, double learning_rate)
    void learn_from_feedback(LearningContext *ctx, LeadFeatures *features,
                             SalesOutcome *outcome)
    
    # Persistência
    int save_weights_to_file(FuzzyWeights *weights, const char *filename)
    int load_weights_from_file(FuzzyWeights *weights, const char *filename)
    int export_weights_json(FuzzyWeights *weights, const char *filename)
    int import_weights_json(FuzzyWeights *weights, const char *filename)
    
    # Métricas
    void calculate_metrics(LearningContext *ctx)
    char* get_performance_report(LearningContext *ctx)
    const char* weight_adjustment_version()


import time
from typing import Dict, List, Tuple, Optional


cdef class NexusLearnContext:
    """
    Contexto de aprendizado do motor Fuzzy.
    
    Gerencia os pesos das 12 regras fuzzy e o histórico de predições.
    """
    cdef LearningContext *c_ctx
    
    def __cinit__(self, int history_capacity=10000):
        """Inicializa o contexto de aprendizado"""
        self.c_ctx = learning_context_init(history_capacity)
        if self.c_ctx == NULL:
            raise MemoryError("Falha ao alocar LearningContext")
    
    def __dealloc__(self):
        """Libera a memória do contexto"""
        if self.c_ctx != NULL:
            learning_context_free(self.c_ctx)
    
    def predict(self, double engagement, double intention, double ai_confidence,
                niche: str = "default") -> Dict:
        """
        Faz uma predição para um novo lead
        
        Args:
            engagement: EMA de engajamento [0, 1]
            intention: Score de intenção [0, 1]
            ai_confidence: Confiança do bot [0, 1]
            niche: Nicho de mercado (até 63 caracteres)
        
        Returns:
            Dict com predicted_score e closure_probability
        """
        cdef LeadFeatures features
        cdef PredictionResult *result
        cdef bytes niche_bytes
        
        features.engagement = engagement
        features.intention = intention
        features.ai_confidence = ai_confidence
        features.timestamp = <long>time.time()
        
        niche_bytes = niche.encode('utf-8')
        if len(niche_bytes) > 63:
            niche_bytes = niche_bytes[:63]
        strcpy(features.niche, niche_bytes)
        
        result = predict_lead(&features, &self.c_ctx.weights)
        if result == NULL:
            raise MemoryError("Falha ao alocar PredictionResult")
        
        cdef dict output = {
            'predicted_score': result.predicted_score,
            'closure_probability': result.closure_probability,
            'rule_activations': [
                result.rule_activations[i] for i in range(12)
            ]
        }
        
        from libc.stdlib cimport free
        free(result)
        
        return output
    
    def learn_from_outcome(self, double engagement, double intention,
                          double ai_confidence, double actual_outcome,
                          was_converted: bool = False, feedback: str = "",
                          niche: str = "default") -> Dict:
        """
        Aprende com o feedback de um resultado de vendas
        
        Args:
            engagement, intention, ai_confidence: mesmos que predict()
            actual_outcome: Resultado real [0=perdida, 0.5=em_andamento, 1=fechada]
            was_converted: Se a venda foi fechada
            feedback: Feedback qualitativo do vendedor
            niche: Nicho de mercado
        
        Returns:
            Dict com erro e métricas atualizadas
        """
        cdef LeadFeatures features
        cdef SalesOutcome outcome
        cdef PredictionResult *prediction
        cdef double error
        cdef bytes feedback_bytes, niche_bytes
        
        # Prepara features
        features.engagement = engagement
        features.intention = intention
        features.ai_confidence = ai_confidence
        features.timestamp = <long>time.time()
        
        niche_bytes = niche.encode('utf-8')
        if len(niche_bytes) > 63:
            niche_bytes = niche_bytes[:63]
        strcpy(features.niche, niche_bytes)
        
        # Prepara outcome
        outcome.actual_outcome = actual_outcome
        outcome.was_converted = 1 if was_converted else 0
        outcome.feedback_timestamp = <long>time.time()
        
        feedback_bytes = feedback.encode('utf-8')
        if len(feedback_bytes) > 255:
            feedback_bytes = feedback_bytes[:255]
        strcpy(outcome.feedback_text, feedback_bytes)
        
        # Aprende do feedback
        learn_from_feedback(self.c_ctx, &features, &outcome)
        
        # Calcula métrica
        calculate_metrics(self.c_ctx)
        
        return {
            'updates_count': self.c_ctx.weights.updates_count,
            'accuracy': self.c_ctx.accuracy,
            'precision': self.c_ctx.precision,
            'recall': self.c_ctx.recall,
            'f1_score': self.c_ctx.f1_score
        }
    
    def get_weights(self) -> List[float]:
        """Retorna os 12 pesos das regras fuzzy"""
        return [self.c_ctx.weights.weights[i] for i in range(12)]
    
    def set_weights(self, list weights):
        """Define manualmente os 12 pesos das regras fuzzy"""
        if len(weights) != 12:
            raise ValueError("Deve ter exatamente 12 pesos")
        
        for i in range(12):
            self.c_ctx.weights.weights[i] = <double>weights[i]
    
    def get_biases(self) -> List[float]:
        """Retorna os 3 biases (score, p_f, confidence)"""
        return [self.c_ctx.weights.biases[i] for i in range(3)]
    
    def get_learning_rate(self) -> float:
        """Retorna a taxa de aprendizado atual"""
        return self.c_ctx.weights.learning_rate
    
    def set_learning_rate(self, double eta):
        """Define a taxa de aprendizado (recomendado: 0.01-0.1)"""
        if eta < 0.001 or eta > 0.5:
            raise ValueError("Learning rate deve estar entre 0.001 e 0.5")
        self.c_ctx.weights.learning_rate = eta
    
    def get_updates_count(self) -> int:
        """Retorna a quantidade de atualizações de peso realizadas"""
        return self.c_ctx.weights.updates_count
    
    def save_to_file(self, filename: str) -> bool:
        """
        Salva os pesos em arquivo binário
        
        Formato: [MAGIC(4)] [12 weights] [3 biases] [learning_rate] [updates_count]
        """
        cdef bytes filename_bytes = filename.encode('utf-8')
        cdef int result = save_weights_to_file(&self.c_ctx.weights, filename_bytes)
        return result == 0
    
    def load_from_file(self, filename: str) -> bool:
        """
        Carrega os pesos de arquivo binário
        """
        cdef bytes filename_bytes = filename.encode('utf-8')
        cdef int result = load_weights_from_file(&self.c_ctx.weights, filename_bytes)
        return result == 0
    
    def export_to_json(self, filename: str) -> bool:
        """
        Exporta os pesos em JSON para debugging e análise
        """
        cdef bytes filename_bytes = filename.encode('utf-8')
        cdef int result = export_weights_json(&self.c_ctx.weights, filename_bytes)
        return result == 0
    
    def get_performance_report(self) -> str:
        """
        Retorna relatório de performance em texto
        """
        calculate_metrics(self.c_ctx)
        cdef const char *report_c = get_performance_report(self.c_ctx)
        
        if report_c == NULL:
            return "Falha ao gerar relatório"
        
        cdef bytes report_bytes = report_c
        cdef str report_py = report_bytes.decode('utf-8')
        
        from libc.stdlib cimport free
        free(<void*>report_c)
        
        return report_py
    
    def get_metrics(self) -> Dict:
        """Retorna as métricas de performance atuais"""
        calculate_metrics(self.c_ctx)
        return {
            'accuracy': self.c_ctx.accuracy,
            'precision': self.c_ctx.precision,
            'recall': self.c_ctx.recall,
            'f1_score': self.c_ctx.f1_score,
            'updates_count': self.c_ctx.weights.updates_count,
            'history_size': self.c_ctx.history_size,
            'avg_training_error': (
                self.c_ctx.weights.total_train_error / max(1, self.c_ctx.weights.updates_count)
            )
        }


def get_version() -> str:
    """Retorna a versão do módulo"""
    cdef const char *version_c = weight_adjustment_version()
    return version_c.decode('utf-8')
