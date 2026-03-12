/**
 * weight_adjustment.c
 * 
 * Implementação do motor de aprendizado automático para Fuzzy Logic.
 * Gerencia o ajuste de pesos das regras fuzzy baseado em feedback de vendas.
 */

#include "weight_adjustment.h"
#include <assert.h>

#define MODULE_VERSION "1.0.0"
#define FUZZY_RULES_COUNT 12
#define SIGMOID_STEEPNESS 5.0

/* ==================== UTILITÁRIOS MATEMÁTICOS ==================== */

/**
 * Função sigmoide: σ(x) = 1 / (1 + e^(-kx))
 * Converte Score (-∞, +∞) em probabilidade (0, 1)
 * k controla a inclinação (default: 5.0)
 */
static double sigmoid(double x, double steepness) {
    double exp_neg = exp(-steepness * x);
    if (exp_neg < 1e-10) return 1.0;
    if (exp_neg > 1e10) return 0.0;
    return 1.0 / (1.0 + exp_neg);
}

/**
 * ReLU: max(0, x)
 */
static double relu(double x) {
    return x > 0.0 ? x : 0.0;
}

/**
 * Clip: limita x no intervalo [min, max]
 */
static double clip(double x, double min_val, double max_val) {
    if (x < min_val) return min_val;
    if (x > max_val) return max_val;
    return x;
}

/* ==================== FUZZIFICAÇÃO ==================== */

/**
 * Membershp function triangular
 * Cria um triângulo em forma de "tenda" entre os pontos a, b, c
 */
double fuzzy_triangular(double x, double a, double b, double c) {
    assert(a <= b && b <= c);
    
    if (x <= a || x >= c) return 0.0;
    if (x == b) return 1.0;
    
    if (x > a && x < b) {
        return (x - a) / (b - a);
    } else {
        return (c - x) / (c - b);
    }
}

/**
 * Trapezoidal membership function
 * Mantém valor 1.0 entre b e c
 */
double fuzzy_trapezoidal(double x, double a, double b, double c, double d) {
    assert(a <= b && b <= c && c <= d);
    
    if (x <= a || x >= d) return 0.0;
    if (x >= b && x <= c) return 1.0;
    
    if (x > a && x < b) {
        return (x - a) / (b - a);
    } else {
        return (d - x) / (d - c);
    }
}

/* ============ FUZZIFICAÇÃO DE ENGAGEMENT ============ */

double fuzzify_engagement_low(double e) {
    // Engagement baixo: 0-40 (pico em 20)
    return fuzzy_triangular(e, 0.0, 0.2, 0.4);
}

double fuzzify_engagement_medium(double e) {
    // Engagement médio: 30-70 (pico em 50)
    return fuzzy_triangular(e, 0.3, 0.5, 0.7);
}

double fuzzify_engagement_high(double e) {
    // Engagement alto: acima de 60 (pico em 100)
    return fuzzy_trapezoidal(e, 0.6, 0.8, 1.0, 1.0);
}

/* ============ FUZZIFICAÇÃO DE INTENÇÃO ============ */

double fuzzify_intention_low(double i) {
    // Intenção baixa: 0-40 (pico em 20)
    return fuzzy_triangular(i, 0.0, 0.2, 0.4);
}

double fuzzify_intention_medium(double i) {
    // Intenção média: 30-70 (pico em 50)
    return fuzzy_triangular(i, 0.3, 0.5, 0.7);
}

double fuzzify_intention_high(double i) {
    // Intenção alta: acima de 60 (pico em 100)
    return fuzzy_trapezoidal(i, 0.6, 0.8, 1.0, 1.0);
}

/* ============ FUZZIFICAÇÃO DE CONFIANÇA IA ============ */

double fuzzify_confidence_low(double u) {
    // Confiança baixa: 0-40
    return fuzzy_triangular(u, 0.0, 0.2, 0.4);
}

double fuzzify_confidence_medium(double u) {
    // Confiança média: 30-70
    return fuzzy_triangular(u, 0.3, 0.5, 0.7);
}

double fuzzify_confidence_high(double u) {
    // Confiança alta: acima de 60
    return fuzzy_trapezoidal(u, 0.6, 0.8, 1.0, 1.0);
}

/* ==================== INICIALIZAÇÃO ==================== */

LearningContext* learning_context_init(int history_capacity) {
    LearningContext *ctx = (LearningContext *)malloc(sizeof(LearningContext));
    if (!ctx) return NULL;
    
    /* Inicializa pesos com valores aleatórios em [0.5, 1.5] */
    srand(time(NULL));
    for (int i = 0; i < FUZZY_RULES_COUNT; i++) {
        ctx->weights.weights[i] = 0.5 + (double)rand() / RAND_MAX;
    }
    
    /* Inicializa biases em 0 */
    for (int i = 0; i < 3; i++) {
        ctx->weights.biases[i] = 0.0;
    }
    
    ctx->weights.learning_rate = 0.05;  /* η (eta) = 5% */
    ctx->weights.updates_count = 0;
    ctx->weights.total_train_error = 0.0;
    
    /* Aloca histórico */
    ctx->history_capacity = history_capacity;
    ctx->history_size = 0;
    ctx->predictions_history = (PredictionResult *)malloc(
        history_capacity * sizeof(PredictionResult)
    );
    ctx->outcomes_history = (SalesOutcome *)malloc(
        history_capacity * sizeof(SalesOutcome)
    );
    
    if (!ctx->predictions_history || !ctx->outcomes_history) {
        learning_context_free(ctx);
        return NULL;
    }
    
    /* Métricas iniciais */
    ctx->accuracy = 0.0;
    ctx->precision = 0.0;
    ctx->recall = 0.0;
    ctx->f1_score = 0.0;
    
    return ctx;
}

void learning_context_free(LearningContext *ctx) {
    if (!ctx) return;
    if (ctx->predictions_history) free(ctx->predictions_history);
    if (ctx->outcomes_history) free(ctx->outcomes_history);
    free(ctx);
}

/* ==================== INFERÊNCIA FUZZY ==================== */

/**
 * Aplica as 12 regras fuzzy em sequência
 * Regra i combina níveis de (E, I, U)
 * 
 * Indexação:
 * 0: (low, low, low)      -> liderança deficiente
 * 1: (low, low, medium)   -> sem sinal
 * 2: (low, low, high)     -> IA chutando
 * 3: (low, medium, low)   -> intenção sem ação
 * 4: (low, medium, medium)
 * 5: (low, medium, high)
 * 6: (medium, low, low)   -> engagem sem intenção
 * 7: (medium, low, medium)
 * 8: (medium, low, high)
 * 9: (medium, medium, medium) -> balanced
 * 10: (medium, high, high)
 * 11: (high, high, high)   -> lead perfeito
 */
void apply_fuzzy_rules(LeadFeatures *features, FuzzyWeights *weights, 
                       PredictionResult *result) {
    assert(features && weights && result);
    
    /* Clipa entradas para [0, 1] */
    double e = clip(features->engagement, 0.0, 1.0);
    double i = clip(features->intention, 0.0, 1.0);
    double u = clip(features->ai_confidence, 0.0, 1.0);
    
    /* Fuzzificação */
    double e_low = fuzzify_engagement_low(e);
    double e_med = fuzzify_engagement_medium(e);
    double e_high = fuzzify_engagement_high(e);
    
    double i_low = fuzzify_intention_low(i);
    double i_med = fuzzify_intention_medium(i);
    double i_high = fuzzify_intention_high(i);
    
    double u_low = fuzzify_confidence_low(u);
    double u_med = fuzzify_confidence_medium(u);
    double u_high = fuzzify_confidence_high(u);
    
    /* Inferência: E ∧ I ∧ U (AND = min) */
    result->rule_activations[0] = fmin(fmin(e_low, i_low), u_low);
    result->rule_activations[1] = fmin(fmin(e_low, i_low), u_med);
    result->rule_activations[2] = fmin(fmin(e_low, i_low), u_high);
    result->rule_activations[3] = fmin(fmin(e_low, i_med), u_low);
    result->rule_activations[4] = fmin(fmin(e_low, i_med), u_med);
    result->rule_activations[5] = fmin(fmin(e_low, i_med), u_high);
    result->rule_activations[6] = fmin(fmin(e_med, i_low), u_low);
    result->rule_activations[7] = fmin(fmin(e_med, i_low), u_med);
    result->rule_activations[8] = fmin(fmin(e_med, i_low), u_high);
    result->rule_activations[9] = fmin(fmin(e_med, i_med), u_med);
    result->rule_activations[10] = fmin(fmin(e_med, i_high), u_high);
    result->rule_activations[11] = fmin(fmin(e_high, i_high), u_high);
}

/**
 * Defuzzificação: Centro de Massa Ponderado (Centroid)
 * Score_weighted = Σ(weights[i] * activation[i]) / Σ(activation[i])
 */
double defuzzify_centroid(double *activations, int num_rules) {
    assert(activations && num_rules > 0);
    
    double numerador = 0.0;
    double denominador = 0.0;
    
    for (int i = 0; i < num_rules; i++) {
        /* Cada regra tem um output padrão proporcional à sua posição */
        double output_value = (double)i / (num_rules - 1); // [0, 1]
        numerador += activations[i] * output_value;
        denominador += activations[i];
    }
    
    if (denominador < 1e-10) return 0.5;  /* valor padrão */
    return numerador / denominador;
}

/**
 * Calcula P_f baseado no Lead Score e no histórico de conversão do nicho
 */
double calculate_closure_probability(double lead_score, const char *niche_memory) {
    /* Por enquanto, usa apenas uma transformação sigmoide do score */
    double p_f = sigmoid(lead_score, SIGMOID_STEEPNESS);
    
    /* TODO: Integrar com Redis para histórico do nicho */
    /* Se niche_memory != NULL, ajusta P_f com taxa de conversão histórica */
    
    return clip(p_f, 0.0, 1.0);
}

/* ==================== PREDIÇÃO ==================== */

PredictionResult* predict_lead(LeadFeatures *features, FuzzyWeights *weights) {
    assert(features && weights);
    
    PredictionResult *result = (PredictionResult *)malloc(sizeof(PredictionResult));
    if (!result) return NULL;
    
    /* Passo 1: Aplicar regras fuzzy */
    apply_fuzzy_rules(features, weights, result);
    
    /* Passo 2: Ponderar pelas regras */
    double numerador = 0.0;
    double denominador = 0.0;
    
    for (int i = 0; i < FUZZY_RULES_COUNT; i++) {
        numerador += weights->weights[i] * result->rule_activations[i];
        denominador += result->rule_activations[i];
    }
    
    if (denominador < 1e-10) {
        numerador = 0.5;
        denominador = 1.0;
    }
    
    double weighted_score = numerador / denominador;
    
    /* Passo 3: Normalizar e aplicar bias */
    result->predicted_score = clip(weighted_score + weights->biases[0], 0.0, 1.0);
    
    /* Passo 4: Calcular P_f */
    result->closure_probability = calculate_closure_probability(
        result->predicted_score, 
        features->niche
    );
    
    return result;
}

/* ==================== APRENDIZADO ==================== */

double calculate_error(double actual_outcome, double predicted_score) {
    return actual_outcome - predicted_score;
}

/**
 * Atualiza os pesos usando a regra: w_i := w_i - η * erro * μ_i
 * 
 * Backpropagation simplificado:
 * - O erro é propagado para cada regra proporcionalmente à sua ativação
 * - Pesos que contribuíram para um erro grande são reduzidos
 * - Pesos associados a acertos são reforçados
 */
void update_weights(FuzzyWeights *weights, double error, 
                    PredictionResult *activations, double learning_rate) {
    assert(weights && activations);
    
    learning_rate = clip(learning_rate, 0.001, 0.5);  /* Sanidade */
    
    /* Atualiza cada peso proporcionalmente ao seu grau de ativação */
    for (int i = 0; i < FUZZY_RULES_COUNT; i++) {
        double activation = activations->rule_activations[i];
        
        /* Gradient: ∂loss/∂w_i ≈ -erro * μ_i */
        double gradient = -error * activation;
        
        /* Update: w_i := w_i - η * gradient */
        double delta = -learning_rate * gradient;
        weights->weights[i] += delta;
        
        /* Clipa peso em [0.01, 10.0] para estabilidade */
        weights->weights[i] = clip(weights->weights[i], 0.01, 10.0);
    }
    
    /* Atualiza bias */
    weights->biases[0] -= learning_rate * error;
    weights->biases[0] = clip(weights->biases[0], -1.0, 1.0);
    
    weights->updates_count++;
    weights->total_train_error += fabs(error);
}

void learn_from_feedback(LearningContext *ctx, LeadFeatures *features,
                         SalesOutcome *outcome) {
    assert(ctx && features && outcome);
    
    /* Prediz o lead */
    PredictionResult *prediction = predict_lead(features, &ctx->weights);
    if (!prediction) return;
    
    /* Calcula o erro: {0, 0.5, 1} real vs prediction */
    double error = calculate_error(outcome->actual_outcome, prediction->predicted_score);
    
    /* Ajusta os pesos */
    update_weights(&ctx->weights, error, prediction, ctx->weights.learning_rate);
    
    /* Armazena no histórico (se houver espaço) */
    if (ctx->history_size < ctx->history_capacity) {
        ctx->predictions_history[ctx->history_size] = *prediction;
        ctx->outcomes_history[ctx->history_size] = *outcome;
        ctx->history_size++;
    }
    
    free(prediction);
}

/* ==================== PERSISTÊNCIA ==================== */

/**
 * Salva pesos em arquivo binário
 * Formato: [MAGIC(4bytes)] [weights[12]] [biases[3]] [learning_rate] [updates_count]
 */
int save_weights_to_file(FuzzyWeights *weights, const char *filename) {
    assert(weights && filename);
    
    FILE *f = fopen(filename, "wb");
    if (!f) return -1;
    
    /* Magic number para validação */
    uint32_t magic = 0xDEADBEEF;
    
    int success = 1;
    success &= fwrite(&magic, sizeof(uint32_t), 1, f) == 1;
    success &= fwrite(weights->weights, sizeof(double), FUZZY_RULES_COUNT, f) == FUZZY_RULES_COUNT;
    success &= fwrite(weights->biases, sizeof(double), 3, f) == 3;
    success &= fwrite(&weights->learning_rate, sizeof(double), 1, f) == 1;
    success &= fwrite(&weights->updates_count, sizeof(long), 1, f) == 1;
    
    fclose(f);
    return success ? 0 : -1;
}

int load_weights_from_file(FuzzyWeights *weights, const char *filename) {
    assert(weights && filename);
    
    FILE *f = fopen(filename, "rb");
    if (!f) return -1;
    
    uint32_t magic;
    int success = 1;
    success &= fread(&magic, sizeof(uint32_t), 1, f) == 1;
    
    if (magic != 0xDEADBEEF) {
        fclose(f);
        return -1;  /* Arquivo inválido */
    }
    
    success &= fread(weights->weights, sizeof(double), FUZZY_RULES_COUNT, f) == FUZZY_RULES_COUNT;
    success &= fread(weights->biases, sizeof(double), 3, f) == 3;
    success &= fread(&weights->learning_rate, sizeof(double), 1, f) == 1;
    success &= fread(&weights->updates_count, sizeof(long), 1, f) == 1;
    
    fclose(f);
    return success ? 0 : -1;
}

/**
 * Exporta em JSON (muy simples, sem libjansson)
 */
int export_weights_json(FuzzyWeights *weights, const char *filename) {
    assert(weights && filename);
    
    FILE *f = fopen(filename, "w");
    if (!f) return -1;
    
    fprintf(f, "{\n");
    fprintf(f, "  \"weights\": [");
    for (int i = 0; i < FUZZY_RULES_COUNT; i++) {
        fprintf(f, "%.6f", weights->weights[i]);
        if (i < FUZZY_RULES_COUNT - 1) fprintf(f, ", ");
    }
    fprintf(f, "],\n");
    
    fprintf(f, "  \"biases\": [%.6f, %.6f, %.6f],\n",
            weights->biases[0], weights->biases[1], weights->biases[2]);
    fprintf(f, "  \"learning_rate\": %.6f,\n", weights->learning_rate);
    fprintf(f, "  \"updates_count\": %ld,\n", weights->updates_count);
    fprintf(f, "  \"total_train_error\": %.6f\n", weights->total_train_error);
    fprintf(f, "}\n");
    
    fclose(f);
    return 0;
}

int import_weights_json(FuzzyWeights *weights, const char *filename) {
    /* TODO: Implementar parsing de JSON (sem dependências externas) */
    return -1;
}

/* ==================== MÉTRICAS ==================== */

void calculate_metrics(LearningContext *ctx) {
    assert(ctx);
    
    if (ctx->history_size == 0) return;
    
    int correct = 0;
    int hot_predicted = 0;
    int hot_actual = 0;
    int true_positives = 0;
    
    /* Threshold: lead "hot" é score > 0.7 */
    double hot_threshold = 0.7;
    
    for (int i = 0; i < ctx->history_size; i++) {
        double pred = ctx->predictions_history[i].predicted_score;
        double actual = ctx->outcomes_history[i].actual_outcome;
        
        /* Accuracy: % de predições corretas (dentro de 0.1) */
        if (fabs(pred - actual) < 0.15) correct++;
        
        /* Precision/Recall: para leads hot (score > 0.7) */
        if (pred > hot_threshold) hot_predicted++;
        if (actual > hot_threshold) hot_actual++;
        if (pred > hot_threshold && actual > hot_threshold) true_positives++;
    }
    
    ctx->accuracy = (double)correct / ctx->history_size;
    ctx->precision = hot_predicted > 0 ? (double)true_positives / hot_predicted : 0.0;
    ctx->recall = hot_actual > 0 ? (double)true_positives / hot_actual : 0.0;
    
    if (ctx->precision + ctx->recall > 0) {
        ctx->f1_score = 2.0 * (ctx->precision * ctx->recall) / (ctx->precision + ctx->recall);
    } else {
        ctx->f1_score = 0.0;
    }
}

char* get_performance_report(LearningContext *ctx) {
    assert(ctx);
    
    calculate_metrics(ctx);
    
    char *report = (char *)malloc(1024);
    if (!report) return NULL;
    
    snprintf(report, 1024,
        "=== NEXUS FUZZY LEARNING REPORT ===\n"
        "Updates: %ld\n"
        "Accuracy: %.2f%%\n"
        "Precision: %.2f%%\n"
        "Recall: %.2f%%\n"
        "F1-Score: %.4f\n"
        "Avg Training Error: %.4f\n"
        "Learning Rate: %.4f\n"
        "History Size: %d\n",
        ctx->weights.updates_count,
        ctx->accuracy * 100.0,
        ctx->precision * 100.0,
        ctx->recall * 100.0,
        ctx->f1_score,
        ctx->weights.total_train_error / fmax(1, ctx->weights.updates_count),
        ctx->weights.learning_rate,
        ctx->history_size
    );
    
    return report;
}

const char* weight_adjustment_version(void) {
    return MODULE_VERSION;
}
