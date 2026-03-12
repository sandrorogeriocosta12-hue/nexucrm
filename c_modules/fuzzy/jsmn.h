/* jsmn.h -- Minimalistic JSON parser in C
 * MIT license
 * see http://zserge.com/jsmn.html
 */
#ifndef JSMN_H
#define JSMN_H

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    JSMN_UNDEFINED = 0,
    JSMN_OBJECT = 1,
    JSMN_ARRAY = 2,
    JSMN_STRING = 3,
    JSMN_PRIMITIVE = 4
} jsmntype_t;

/* JSON token description. Contains type (object, array, string etc.),
 * start and end position in JSON data, and the number of child tokens.
 */
typedef struct {
    jsmntype_t type;
    int start;
    int end;
    int size;
    int parent;
} jsmntok_t;

/* Parser state. Contains an array of tokens available. Also stores the
 * offset in the JSON string and current token position.
 */
typedef struct {
    unsigned int pos;     /* offset in the JSON string */
    unsigned int toknext; /* next token to allocate */
    int toksuper;         /* superior token node, e.g parent object or array */
} jsmn_parser;

/* Create JSON parser and initialize it. */
void jsmn_init(jsmn_parser *parser);

/* Run JSON parser. It parses a JSON data string into and array of tokens, each
 * describing a single JSON object. "tokens" must be an array of pointers to
 * jsmntok_t objects available in memory. If the number of tokens provided is
 * not sufficient, JSMN_ERROR_NOMEM will be returned. */
int jsmn_parse(jsmn_parser *parser, const char *js, size_t len,
               jsmntok_t *tokens, unsigned int num_tokens);

/* Possible error codes returned by jsmn_parse. */
#define JSMN_ERROR_NOMEM -1
#define JSMN_ERROR_INVAL -2
#define JSMN_ERROR_PART  -3

#ifdef __cplusplus
}
#endif

#endif /* JSMN_H */
