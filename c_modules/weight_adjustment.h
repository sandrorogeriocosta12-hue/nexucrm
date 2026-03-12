/**
 * weight_adjustment.h
 * 
 * Módulo de ajuste automático de pesos para o motor Fuzzy do Nexus Service.
 * Implementa o loop de aprendizado baseado em erro com gradiente descendente.
 * 
 * Arquitetura:
 * - Fuzzificação: E (Engagement), I (Intention), U (AI Confidence)
 * - Inferência: LeadScore = Σ(w_i * μ_i) / Σ(μ_i)
 * - Probabilidade de Fechamento: P_f = sigmoid(LeadScore + historial)
 * - Aprendizado: w_i := w_i - η * ∇Error
 * 
 * Taxa de aprendizado (learning rate): η = 0.05 (padrão)
 */

#ifndef WEIGHT_ADJUSTMENT_H
#define WEIGHT_ADJUSTMENT_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ==================== TIPOS E ESTRUTURAS ==================== */

/**
 * Representa um ponto de dados de entrada (features do lead)
 */
typedef struct {
    double engagement;      /* E: EMA do engagement [0, 1] */
    double intention;       /* I: Score de intenção de fechamento [0, 1] */
    double ai_confidence;   /* U: Confiança das respostas do bot [0, 1] */
    char niche[64];         /* Nicho de mercado para histórico contextual */
    long timestamp;         /* Timestamp do evento */
} LeadFeatures;

/**
 * Resultado da predição do sistema
 */
typedef struct {
    double predicted_score;     /* Score predito (0-1) */
    double closure_probability; /* P_f predita (0-1) */
    double rule_activations[12]; /* Graus de ativação das 12 regras fuzzy */
} PredictionResult;

/**
 * Feedback de resultado real (vendedor marcou venda como aberta/perdida)
 */
typedef struct {
    double actual_outcome;    /* 0.0 = Perdida, 0.5 = Em Andamento, 1.0 = Fechada */
    int was_converted;        /* Boolean: vendedor fechou a venda? */
    char feedback_text[256];  /* Feedback qualitativo do vendedor */
    long feedback_timestamp;  /* Quando o feedback foi registrado */
} SalesOutcome;

/**
 * Pesos das 12 regras fuzzy do motor
 * Cada peso controla a influência de uma combinação (E, I, U) no score final
 */
typedef struct {
    double weights[12];      /* w_i para cada regra */
    double biases[3];        /* b para os 3 outputs (score, P_f, confidence) */
    double learning_rate;    /* η (eta) - taxa de aprendizado adaptativa */
    long updates_count;      /* Quantas vezes os pesos foram atualizados */
    double total_train_error; /* Erro acumulado para monitoramento */
} FuzzyWeights;

/**
 * Contexto completo do aprendizado
 * Mantém histórico de predições e feedback para cálculo de métricas
 */
typedef struct {
    FuzzyWeights weights;
    
    /* Histórico para validação */
    PredictionResult *predictions_history;
    SalesOutcome *outcomes_history;
    int history_size;
    int history_capacity;
    
    /* Métricas de performance */
    double accuracy;           /* Taxa de acerto das predições */
    double precision;          /* Precisão em leads hot (score > 0.7) */
    double recall;             /* Recall em leads hot */
    double f1_score;           /* F1 = 2 * (precision * recall) / (precision + recall) */
} LearningContext;

/* ==================== FUNÇÕES PRINCIPAIS ==================== */

/**
 * Inicializa o contexto de aprendizado com pesos aleatórios [0.5, 1.5]
 */
LearningContext* learning_context_init(int history_capacity);

/**
 * Libera memória do contexto de aprendizado
 */
void learning_context_free(LearningContext *ctx);

/**
 * ============ FUZZIFICAÇÃO ============
 * Converte os dados brutos em graus de pertinência [0, 1]
 */

/**
 * Funções de pertinência fuzzy
 * Tipo triangular: (x, a=esquerda, b=pico, c=direita)
 */
double fuzzy_triangular(double x, double a, double b, double c);
double fuzzy_trapezoidal(double x, double a, double b, double c, double d);

/**
 * Fuzzificação de cada entrada
 */
double fuzzify_engagement_low(double e);
double fuzzify_engagement_medium(double e);
double fuzzify_engagement_high(double e);

double fuzzify_intention_low(double i);
double fuzzify_intention_medium(double i);
double fuzzify_intention_high(double i);

double fuzzify_confidence_low(double u);
double fuzzify_confidence_medium(double u);
double fuzzify_confidence_high(double u);

/* ============ INFERÊNCIA FUZZY ============ */

/**
 * Aplica as 12 regras fuzzy e retorna os graus de ativação
 * Regras combinam (E_level, I_level, U_level) onde cada level ∈ {low, medium, high}
 * 
 * Os 12 pesos são indexados como:
 * [0]  = (low, low, low)
 * [1]  = (low, low, medium)
 * [2]  = (low, low, high)
 * [3]  = (low, medium, low)
 * ...
 * [11] = (high, high, high)
 */
void apply_fuzzy_rules(LeadFeatures *features, FuzzyWeights *weights, 
                       PredictionResult *result);

/**
 * Defuzzificação: converte graus de ativação em um score (0-1)
 */
double defuzzify_centroid(double *activations, int num_rules);

/**
 * Calcula a probabilidade de fechamento baseada no score e histórico
 * P_f = sigmoid(score + historical_factor)
 */
double calculate_closure_probability(double lead_score, const char *niche_memory);

/* ============ LOOP DE APRENDIZADO ============ */

/**
 * Realiza uma predição completa para um lead
 * Retorna LeadScore e P_f com todos os detalhes da ativação das regras
 */
PredictionResult* predict_lead(LeadFeatures *features, FuzzyWeights *weights);

/**
 * Calcula o erro: Erro = |real - predito|
 */
double calculate_error(double actual_outcome, double predicted_score);

/**
 * Ajusta os pesos usando a regra de aprendizado (gradient descent)
 * Nova regra: w_i := w_i - η * erro * μ_i
 * 
 * Onde:
 * - η é a taxa de aprendizado (learning_rate)
 * - erro é a diferença entre resultado real e predito
 * - μ_i é o grau de ativação da regra i
 */
void update_weights(FuzzyWeights *weights, double error, 
                    PredictionResult *activations, double learning_rate);

/**
 * Processa um feedback e atualiza os pesos
 */
void learn_from_feedback(LearningContext *ctx, LeadFeatures *features,
                         SalesOutcome *outcome);

/* ============ PERSISTÊNCIA ============ */

/**
 * Salva os pesos em arquivo binário para reutilização
 * Formato: [header(4)] [12 weights] [3 biases] [learning_rate] [updates_count]
 */
int save_weights_to_file(FuzzyWeights *weights, const char *filename);

/**
 * Carrega os pesos do arquivo binário
 */
int load_weights_from_file(FuzzyWeights *weights, const char *filename);

/**
 * Exporta pesos em formato JSON para debugging
 */
int export_weights_json(FuzzyWeights *weights, const char *filename);

/**
 * Importa pesos de JSON (útil para A/B testing e rollback)
 */
int import_weights_json(FuzzyWeights *weights, const char *filename);

/* ============ MÉTRICAS E MONITORAMENTO ============ */

/**
 * Calcula métricas de performance
 * - Accuracy: % de predições corretas
 * - Precision: % de true positives entre hot leads preditos
 * - Recall: % de hot leads reais que foram preditos como hot
 * - F1: Média harmônica de precision e recall
 */
void calculate_metrics(LearningContext *ctx);

/**
 * Retorna um string com relatório de performance
 * Use free() para liberar a memória depois
 */
char* get_performance_report(LearningContext *ctx);

/**
 * Retorna a versão do módulo
 */
const char* weight_adjustment_version(void);

#endif /* WEIGHT_ADJUSTMENT_H */
