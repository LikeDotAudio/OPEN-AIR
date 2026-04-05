#include <iostream>
#include <vector>
#include <cstring>
#include <iomanip>

// Use volatile to prevent compiler from optimizing away the reads/writes
volatile char* p_secret;

void fill_stack() {
    char secret[1290];
    std::memset(secret, 0xAA, sizeof(secret));
    p_secret = secret; // Capture address (though it will be invalid after return)
}

void leak_check() {
    char buffer[1290];
    // We do NOT initialize buffer. We want to see if it contains 0xAA from previous stack frame.
    int leaked = 0;
    for(int i = 0; i < 1290; ++i) {
        if ((unsigned char)buffer[i] == 0xAA) {
            leaked++;
        }
    }
    std::cout << "Leaked bytes from previous stack frame: " << leaked << " / 1290" << std::endl;
    
    if (leaked > 1000) {
        std::cout << "VULNERABILITY CONFIRMED: Stack retention detected." << std::endl;
    } else {
        std::cout << "Vulnerability not reproduced (stack might have been reused/cleared by OS/Compiler)." << std::endl;
    }
}

int main() {
    std::cout << "Running PoC for ZR-001 (STACK_RETENTION)..." << std::endl;
    fill_stack();
    leak_check();
    return 0;
}
