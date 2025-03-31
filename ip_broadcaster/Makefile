CC=arm-linux-gnueabihf-gcc
CFLAGS=-Wall -Wextra -O2
TARGET=icmp_broadcast

all: $(TARGET)

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $(TARGET) main.c

clean:
	rm -f $(TARGET)
