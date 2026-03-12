CC = gcc
CFLAGS = -O3 -fPIC -Wall
LDFLAGS = -shared
TARGET = libfuzzy.so
SRCS = fuzzy_logic.c
OBJS = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean
