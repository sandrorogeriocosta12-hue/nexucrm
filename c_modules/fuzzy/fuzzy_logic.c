#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "jsmn.h"
#include "fuzzy_logic.h"

// Função de pertinência triangular
static double triangular(double x, double a, double b, double c) {
    if (x <= a || x >= c) return 0.0;
    if (x == b) return 1.0;
    if (x > a && x < b) return (x - a) / (b - a);
    return (c - x) / (c - b);
}

// Carrega sistema fuzzy de um arquivo JSON (agora usando jsmn para parser)
// Regras, variáveis e conjuntos são definidos no arquivo fornecido.
FuzzySystem* fuzzy_system_load(const char* filename) {
    FILE* f = fopen(filename, "r");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long flen = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *json = malloc(flen + 1);
    if (!json) { fclose(f); return NULL; }
    fread(json, 1, flen, f);
    json[flen] = '\0';
    fclose(f);

    jsmn_parser parser;
    jsmntok_t tokens[1024];
    jsmn_init(&parser);
    int tokn = jsmn_parse(&parser, json, flen, tokens, 1024);
    if (tokn < 0) {
        free(json);
        return NULL;
    }

    // helper for comparing
    #define jsoneq(js, tok, s) \
        ((tok)->type == JSMN_STRING && \
         (int)strlen(s) == (tok)->end - (tok)->start && \
         strncmp((js) + (tok)->start, s, (tok)->end - (tok)->start) == 0)

    FuzzySystem *sys = malloc(sizeof(FuzzySystem));
    sys->num_variables = 0;
    sys->variables = NULL;
    sys->num_rules = 0;
    sys->rules = NULL;

    // iterate through top-level tokens looking for "variables" and "rules"
    for (int i = 1; i < tokn; i++) {
        if (jsoneq(json, &tokens[i], "variables")) {
            jsmntok_t *arr = &tokens[i+1];
            if (arr->type == JSMN_ARRAY) {
                int count = arr->size;
                sys->num_variables = count;
                sys->variables = calloc(count, sizeof(FuzzyVariable));
                int idx = i+2; // first element
                for (int v = 0; v < count; v++) {
                    // tokens[idx] is object
                    jsmntok_t *obj = &tokens[idx];
                    int len_obj = obj->size;
                    idx++;
                    FuzzyVariable *var = &sys->variables[v];
                    var->sets = NULL;
                    var->num_sets = 0;
                    for (int j = 0; j < len_obj; j++) {
                        jsmntok_t *key = &tokens[idx++];
                        if (jsoneq(json, key, "name")) {
                            jsmntok_t *val = &tokens[idx++];
                            int l = val->end - val->start;
                            var->name = strndup(json + val->start, l);
                        } else if (jsoneq(json, key, "min")) {
                            jsmntok_t *val = &tokens[idx++];
                            char buf[32];
                            int l = val->end - val->start;
                            strncpy(buf, json+val->start, l);
                            buf[l] = '\0';
                            var->min = atof(buf);
                        } else if (jsoneq(json, key, "max")) {
                            jsmntok_t *val = &tokens[idx++];
                            char buf[32];
                            int l = val->end - val->start;
                            strncpy(buf, json+val->start, l);
                            buf[l] = '\0';
                            var->max = atof(buf);
                        } else if (jsoneq(json, key, "sets")) {
                            jsmntok_t *setarr = &tokens[idx++];
                            int scount = setarr->size;
                            var->num_sets = scount;
                            var->sets = calloc(scount, sizeof(FuzzySet));
                            int sidx = idx;
                            for (int s = 0; s < scount; s++) {
                                jsmntok_t *setobj = &tokens[sidx++];
                                int slen = setobj->size;
                                FuzzySet *set = &var->sets[s];
                                for (int k = 0; k < slen; k++) {
                                    jsmntok_t *kkey = &tokens[sidx++];
                                    if (jsoneq(json, kkey, "name")) {
                                        jsmntok_t *kval = &tokens[sidx++];
                                        int l = kval->end - kval->start;
                                        set->name = strndup(json+kval->start, l);
                                    } else if (jsoneq(json, kkey, "a")) {
                                        jsmntok_t *kval = &tokens[sidx++];
                                        char buf[32]; int l = kval->end - kval->start;
                                        strncpy(buf, json+kval->start, l); buf[l]='\0';
                                        set->a = atof(buf);
                                    } else if (jsoneq(json, kkey, "b")) {
                                        jsmntok_t *kval = &tokens[sidx++];
                                        char buf[32]; int l = kval->end - kval->start;
                                        strncpy(buf, json+kval->start, l); buf[l]='\0';
                                        set->b = atof(buf);
                                    } else if (jsoneq(json, kkey, "c")) {
                                        jsmntok_t *kval = &tokens[sidx++];
                                        char buf[32]; int l = kval->end - kval->start;
                                        strncpy(buf, json+kval->start, l); buf[l]='\0';
                                        set->c = atof(buf);
                                    } else {
                                        // skip value
                                        sidx++;
                                    }
                                }
                            }
                            idx = sidx;
                        } else {
                            // skip unknown key value
                            idx++;
                        }
                    }
                }
            }
        } else if (jsoneq(json, &tokens[i], "rules")) {
            jsmntok_t *arr = &tokens[i+1];
            if (arr->type == JSMN_ARRAY) {
                int rcount = arr->size;
                sys->num_rules = rcount;
                sys->rules = calloc(rcount, sizeof(FuzzyRule));
                int ridx = i+2;
                for (int r = 0; r < rcount; r++) {
                    jsmntok_t *robj = &tokens[ridx++];
                    int rlen = robj->size;
                    // allocate antecedents later when known
                    for (int j = 0; j < rlen; j++) {
                        jsmntok_t *rkey = &tokens[ridx++];
                        if (jsoneq(json, rkey, "antecedents")) {
                            jsmntok_t *arant = &tokens[ridx++];
                            int antic = arant->size;
                            sys->rules[r].num_antecedents = antic;
                            sys->rules[r].antecedents = calloc(antic, sizeof(FuzzyAntecedent));
                            int aidx = ridx;
                            for (int a = 0; a < antic; a++) {
                                jsmntok_t *antobj = &tokens[aidx++];
                                int alen = antobj->size;
                                for (int k = 0; k < alen; k++) {
                                    jsmntok_t *ak = &tokens[aidx++];
                                    if (jsoneq(json, ak, "var")) {
                                        jsmntok_t *av = &tokens[aidx++];
                                        int l = av->end - av->start;
                                        sys->rules[r].antecedents[a].var_name = strndup(json+av->start,l);
                                    } else if (jsoneq(json, ak, "set")) {
                                        jsmntok_t *av = &tokens[aidx++];
                                        int l = av->end - av->start;
                                        sys->rules[r].antecedents[a].set_name = strndup(json+av->start,l);
                                    } else {
                                        aidx++;
                                    }
                                }
                            }
                            ridx = aidx;
                        } else if (jsoneq(json, rkey, "consequent")) {
                            jsmntok_t *cobj = &tokens[ridx++];
                            int clen = cobj->size;
                            for (int k = 0; k < clen; k++) {
                                jsmntok_t *ck = &tokens[ridx++];
                                if (jsoneq(json, ck, "var")) {
                                    jsmntok_t *cv = &tokens[ridx++];
                                    int l = cv->end - cv->start;
                                    sys->rules[r].consequent.var_name = strndup(json+cv->start,l);
                                } else if (jsoneq(json, ck, "set")) {
                                    jsmntok_t *cv = &tokens[ridx++];
                                    int l = cv->end - cv->start;
                                    sys->rules[r].consequent.set_name = strndup(json+cv->start,l);
                                } else if (jsoneq(json, ck, "weight")) {
                                    jsmntok_t *cv = &tokens[ridx++];
                                    char buf[32]; int l = cv->end - cv->start;
                                    strncpy(buf, json+cv->start, l);
                                    buf[l] = '\0';
                                    sys->rules[r].consequent.weight = atof(buf);
                                } else {
                                    ridx++;
                                }
                            }
                            if (sys->rules[r].consequent.weight == 0) {
                                sys->rules[r].consequent.weight = 1.0;
                            }
                        } else {
                            // skip value
                            ridx++;
                        }
                    }
                }
            }
        }
    }
    free(json);
    return sys;
}

// Avalia o sistema para uma variável de saída (ex: "score") dado um array de entradas

double fuzzy_system_evaluate(FuzzySystem* sys, const char* out_var, double* inputs) {
    // Para cada regra, calcula o grau de ativação (mínimo dos antecedentes)
    double* activation = (double*)malloc(sys->num_rules * sizeof(double));
    for (int r = 0; r < sys->num_rules; r++) {
        double min_val = 1.0;
        for (int a = 0; a < sys->rules[r].num_antecedents; a++) {
            FuzzyAntecedent* ant = &sys->rules[r].antecedents[a];
            int var_idx = -1;
            for (int v = 0; v < sys->num_variables; v++) {
                if (strcmp(sys->variables[v].name, ant->var_name) == 0) {
                    var_idx = v;
                    break;
                }
            }
            if (var_idx == -1) continue;
            double input_val = inputs[var_idx];
            FuzzySet* set = NULL;
            for (int s = 0; s < sys->variables[var_idx].num_sets; s++) {
                if (strcmp(sys->variables[var_idx].sets[s].name, ant->set_name) == 0) {
                    set = &sys->variables[var_idx].sets[s];
                    break;
                }
            }
            if (!set) continue;
            double pert = triangular(input_val, set->a, set->b, set->c);
            if (pert < min_val) min_val = pert;
        }
        activation[r] = min_val;
    }
    // Defuzzificação pelo centro de massa
    double numerador = 0.0, denominador = 0.0;
    for (int r = 0; r < sys->num_rules; r++) {
        const char* set_name = sys->rules[r].consequent.set_name;
        double centro = 0;
        if (strcmp(set_name, "baixo") == 0) centro = 20;
        else if (strcmp(set_name, "medio") == 0) centro = 50;
        else if (strcmp(set_name, "alto") == 0) centro = 80;
        numerador += activation[r] * centro;
        denominador += activation[r];
    }
    free(activation);
    if (denominador == 0) return 50.0;
    return numerador / denominador;
}

void fuzzy_system_free(FuzzySystem* sys) {
    for (int v = 0; v < sys->num_variables; v++) {
        free(sys->variables[v].name);
        free(sys->variables[v].sets);
    }
    free(sys->variables);
    for (int r = 0; r < sys->num_rules; r++) {
        free(sys->rules[r].antecedents);
    }
    free(sys->rules);
    free(sys);
}
