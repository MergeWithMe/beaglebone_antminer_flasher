#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netinet/ip_icmp.h>
#include <time.h>
#include <fcntl.h>
#include <sys/types.h>
#include <ifaddrs.h>
#include <net/if.h>

#define IP_FOUND "IP_FOUND"
#define IP_FOUND_ACK "IP_FOUND_ACK"
#define PORT 6969

// Compute ICMP checksum
unsigned short checksum(void *b, int len) {
    unsigned short *buf = b;
    unsigned int sum = 0;
    unsigned short result;
    for (sum = 0; len > 1; len -= 2) {
        sum += *buf++;
    }
    if (len == 1) {
        sum += *(unsigned char *)buf;
    }
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    result = ~sum;
    return result;
}

// Function to calculate the broadcast address based on the local IP and netmask

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <ifaddrs.h>

char* get_broadcast_address() {
    struct ifaddrs *ifaddr, *ifa;
    char *broadcast_ip = malloc(INET_ADDRSTRLEN);

    if (getifaddrs(&ifaddr) == -1) {
        perror("getifaddrs");
        return NULL;
    }

    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        if (ifa->ifa_addr != NULL && ifa->ifa_addr->sa_family == AF_INET) {
            // Skip loopback interface (127.0.0.1)
            if (strcmp(ifa->ifa_name, "lo") == 0) {
                continue;
            }

            struct sockaddr_in *sa = (struct sockaddr_in *) ifa->ifa_addr;
            struct sockaddr_in *netmask = (struct sockaddr_in *) ifa->ifa_netmask;

            if (sa != NULL && netmask != NULL) {
                // Debugging: print the IP and netmask
                printf("Interface: %s\n", ifa->ifa_name);
                printf("IP: %s\n", inet_ntoa(sa->sin_addr));
                printf("Netmask: %s\n", inet_ntoa(netmask->sin_addr));

                // Calculate the broadcast address by ORing the IP with the negated netmask
                struct sockaddr_in broadcast_addr;
                broadcast_addr.sin_family = AF_INET;

                broadcast_addr.sin_addr.s_addr = sa->sin_addr.s_addr | (~netmask->sin_addr.s_addr);

                // Debugging: print the broadcast address
                printf("Calculated Broadcast: %s\n", inet_ntoa(broadcast_addr.sin_addr));

                // Convert to string and return
                strcpy(broadcast_ip, inet_ntoa(broadcast_addr.sin_addr));
                freeifaddrs(ifaddr);
                return broadcast_ip;
            }
        }
    }
    freeifaddrs(ifaddr);
    return NULL; // Broadcast address not found
}


void send_icmp_broadcast() {
    while (1) {
        int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
        if (sockfd < 0) {
            perror("socket failed, retrying...");
            sleep(5);
            continue;
        }
        
        int enable_broadcast = 1;
        if (setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &enable_broadcast, sizeof(enable_broadcast)) < 0) {
            perror("setsockopt failed, retrying...");
            close(sockfd);
            sleep(5);
            continue;
        }
        
        char *broadcast_ip = get_broadcast_address();
        if (broadcast_ip == NULL) {
            perror("Unable to determine broadcast address");
            close(sockfd);
            sleep(5);
            continue;
        }

        struct sockaddr_in broadcast_addr;
        memset((void*)&broadcast_addr, 0, sizeof(struct sockaddr_in));
        broadcast_addr.sin_family = AF_INET;
        broadcast_addr.sin_addr.s_addr = inet_addr(broadcast_ip);
        broadcast_addr.sin_port = htons(PORT);

        while (1) {
            if (sendto(sockfd, IP_FOUND, strlen(IP_FOUND), 0, (struct sockaddr*) &broadcast_addr, sizeof(broadcast_addr)) < 0) {
                perror("sendto failed, retrying...");
                sleep(5);
                continue;
            }
            sleep(2);
        }
        close(sockfd);
        free(broadcast_ip);  // Free dynamically allocated memory
    }
}

int main(int argc, char *argv[]) {
    char *pid_file = NULL;
    if (argc == 3 && strcmp(argv[1], "-p") == 0) {
        pid_file = argv[2];
    }
    
    if(pid_file != NULL) {
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork failed");
            exit(1);
        }
        if (pid > 0) {
            if (pid_file) {
                FILE *fp = fopen(pid_file, "w");
                if (fp) {
                    fprintf(fp, "%d\n", pid);
                    fclose(fp);
                } else {
                    perror("Failed to create PID file");
                }
            }
            exit(0); // Parent exits, child continues
        }
        
        setsid();
        chdir("/");
        close(STDIN_FILENO);
        close(STDOUT_FILENO);
        close(STDERR_FILENO);
    }
    
    send_icmp_broadcast();
    return 0;
}
