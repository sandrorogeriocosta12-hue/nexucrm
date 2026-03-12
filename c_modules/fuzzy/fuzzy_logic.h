#ifndef FUZZY_LOGIC_H
#define FUZZY_LOGIC_H

#include <stddef.h>

typedef struct {
    char* name;
    double a, b, c;  // parâmetros da função triangular
} FuzzySet;

typedef struct {
    char* var_name;
    char* set_name;
    double value;
} FuzzyAntecedent;

typedef struct {
    char* var_name;
    char* set_name;
    double weight;
} FuzzyConsequent;

typedef struct {
    FuzzyAntecedent* antecedents;
    int num_antecedents;
    FuzzyConsequent consequent;
} FuzzyRule;

typedef struct {
    char* name;
    double min, max;
    FuzzySet* sets;
    int num_sets;
} FuzzyVariable;

typedef struct {
    FuzzyVariable* variables;
    int num_variables;
    FuzzyRule* rules;
    int num_rules;
} FuzzySystem;

// Funções públicas
FuzzySystem* fuzzy_system_load(const char* filename);
double fuzzy_system_evaluate(FuzzySystem* sys, const char* var_name, double* inputs);
void fuzzy_system_free(FuzzySystem* sys);

#endif
