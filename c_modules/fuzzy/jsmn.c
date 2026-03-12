/* jsmn.c -- Minimalistic JSON parser in C
 * MIT license
 * see http://zserge.com/jsmn.html
 */
#include <string.h>
#include <stdio.h>
#include "jsmn.h"

static int jsmn_alloc_token(jsmn_parser *parser, jsmntok_t *tokens,
                            size_t num_tokens) {
    jsmntok_t *tok;
    if (parser->toknext >= num_tokens) {
        return JSMN_ERROR_NOMEM;
    }
    tok = &tokens[parser->toknext++];
    tok->start = tok->end = -1;
    tok->size = 0;
    tok->parent = -1;
    return parser->toknext - 1;
}

static void jsmn_fill_token(jsmntok_t *token, jsmntype_t type,
                            int start, int end) {
    token->type = type;
    token->start = start;
    token->end = end;
    token->size = 0;
}

static int jsmn_parse_primitive(jsmn_parser *parser, const char *js,
                                size_t len, jsmntok_t *tokens,
                                size_t num_tokens) {
    jsmntok_t *token;
    int start = parser->pos;

    for (; parser->pos < len && js[parser->pos] != '\0'; parser->pos++) {
        switch (js[parser->pos]) {
            case '\t': case '\r': case '\n': case ' ':
            case ',': case ']': case '}':
                goto found;
        }
        if (js[parser->pos] < 32) {
            parser->pos = start;
            return JSMN_ERROR_INVAL;
        }
    }
found:
    if (tokens == NULL) {
        parser->pos--;
        return 0;
    }
    int idx = jsmn_alloc_token(parser, tokens, num_tokens);
    if (idx < 0) return idx;
    token = &tokens[idx];
    jsmn_fill_token(token, JSMN_PRIMITIVE, start, parser->pos);
    token->parent = parser->toksuper;
    parser->pos--;
    return 0;
}

static int jsmn_parse_string(jsmn_parser *parser, const char *js,
                            size_t len, jsmntok_t *tokens,
                            size_t num_tokens) {
    jsmntok_t *token;
    int start = parser->pos;

    parser->pos++;
    for (; parser->pos < len && js[parser->pos] != '\0'; parser->pos++) {
        char c = js[parser->pos];
        if (c == '"') {
            if (tokens == NULL) return 0;
            int idx = jsmn_alloc_token(parser, tokens, num_tokens);
            if (idx < 0) return idx;
            token = &tokens[idx];
            jsmn_fill_token(token, JSMN_STRING, start+1, parser->pos);
            token->parent = parser->toksuper;
            return 0;
        }
        if (c == '\\') {
            parser->pos++;
            if (parser->pos == len) break;
        }
    }
    parser->pos = start;
    return JSMN_ERROR_PART;
}

void jsmn_init(jsmn_parser *parser) {
    parser->pos = 0;
    parser->toknext = 0;
    parser->toksuper = -1;
}

int jsmn_parse(jsmn_parser *parser, const char *js, size_t len,
               jsmntok_t *tokens, unsigned int num_tokens) {
    int r;
    int i;
    for (; parser->pos < len && js[parser->pos] != '\0'; parser->pos++) {
        char c = js[parser->pos];
        switch (c) {
            case '{':
            case '[':
                r = jsmn_alloc_token(parser, tokens, num_tokens);
                if (r < 0) return r;
                tokens[r].type = (c == '{' ? JSMN_OBJECT : JSMN_ARRAY);
                tokens[r].start = parser->pos;
                tokens[r].parent = parser->toksuper;
                parser->toksuper = r;
                break;
            case '}':
            case ']':
                if (parser->toknext < 1) return JSMN_ERROR_INVAL;
                for (i = parser->toknext - 1; i >= 0; i--) {
                    if (tokens[i].start != -1 && tokens[i].end == -1) {
                        if ((tokens[i].type == JSMN_OBJECT && c == '}') ||
                            (tokens[i].type == JSMN_ARRAY && c == ']')) {
                            tokens[i].end = parser->pos + 1;
                            parser->toksuper = tokens[i].parent;
                            break;
                        }
                    }
                }
                break;
            case '"':
                r = jsmn_parse_string(parser, js, len, tokens, num_tokens);
                if (r < 0) return r;
                break;
            case '\t': case '\r': case '\n': case ' ':
                break;
            case ':':
                parser->toksuper = parser->toknext - 1;
                break;
            case ',':
                if (parser->toksuper != -1 &&
                    tokens[parser->toksuper].type != JSMN_ARRAY &&
                    tokens[parser->toksuper].type != JSMN_OBJECT) {
                    parser->toksuper = tokens[parser->toksuper].parent;
                }
                break;
            default:
                r = jsmn_parse_primitive(parser, js, len, tokens, num_tokens);
                if (r < 0) return r;
                break;
        }
    }
    for (i = parser->toknext - 1; i >= 0; i--) {
        if (tokens[i].start != -1 && tokens[i].end == -1) {
            return JSMN_ERROR_PART;
        }
    }
    return parser->toknext;
}
