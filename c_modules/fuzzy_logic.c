// fuzzy_logic.c
#include <stdio.h>
#include <math.h>

// Função de pertinência triangular
static double triangular(double x, double a, double b, double c) {
    if (x <= a || x >= c) return 0.0;
    if (x == b) return 1.0;
    if (x > a && x < b) return (x - a) / (b - a);
    return (c - x) / (c - b);
}

// Regras fuzzy: LeadScore = f(engagement, likelihood)
// Regra 1: Se engagement é ALTO e likelihood é ALTA então score é ALTO
// Regra 2: Se engagement é BAIXO então score é BAIXO
// etc...

double compute_lead_score(double engagement, double likelihood) {
    // Conjuntos fuzzy para engagement (0-100)
    double eng_baixo = triangular(engagement, 0, 0, 50);
    double eng_medio = triangular(engagement, 30, 50, 70);
    double eng_alto  = triangular(engagement, 50, 100, 100);

    // Conjuntos fuzzy para likelihood (0-100)
    double like_baixo = triangular(likelihood, 0, 0, 40);
    double like_medio = triangular(likelihood, 20, 50, 80);
    double like_alto  = triangular(likelihood, 60, 100, 100);

    // Aplicar regras (método de Mamdani simplificado)
    double score_alto  = fmin(eng_alto, like_alto);   // regra 1
    double score_medio = fmin(eng_medio, like_medio); // regra 2
    double score_baixo = fmax(eng_baixo, like_baixo); // regra 3 (OU)

    // Defuzzificação: centro de massa ponderado
    double numerador = score_baixo * 20 + score_medio * 50 + score_alto * 80;
    double denominador = score_baixo + score_medio + score_alto;
    if (denominador == 0) return 50.0; // valor padrão
    return numerador / denominador;
}
