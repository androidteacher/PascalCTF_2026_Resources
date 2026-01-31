#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

// MT19937 Parameters
#define N 624
#define M 397
#define MATRIX_A 0x9908B0DF
#define UPPER_MASK 0x80000000
#define LOWER_MASK 0x7FFFFFFF

uint32_t mt[N];
int mti = N + 1;

void init_genrand(uint32_t s) {
    mt[0] = s & 0xFFFFFFFF;
    for (mti = 1; mti < N; mti++) {
        // 1812433253 * (mt[i-1] ^ (mt[i-1] >> 30)) + i
        mt[mti] = (1812433253UL * (mt[mti - 1] ^ (mt[mti - 1] >> 30)) + mti);
        mt[mti] &= 0xFFFFFFFF; // for >32 bit machines
    }
}

// Generate the next state (twist) is embedded in creation or next call
// The python code initializes, then twists ONLY when index >= N.
// But python init sets index = N. So first call triggers twist.

void twist() {
    int i;
    uint32_t y;
    uint32_t mag01[2] = {0x0UL, MATRIX_A};
    /* mag01[x] = x * MATRIX_A  for x=0,1 */

    for (i = 0; i < N - 1; i++) {
        y = (mt[i] & UPPER_MASK) | (mt[i + 1] & LOWER_MASK);
        mt[i] = mt[(i + M) % N] ^ (y >> 1) ^ mag01[y & 0x1];
    }
    // Last element wrap around
    y = (mt[N - 1] & UPPER_MASK) | (mt[0] & LOWER_MASK);
    mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ mag01[y & 0x1];
    
    mti = 0;
}

uint32_t extract_number() {
    if (mti >= N) {
        twist();
    }

    uint32_t y = mt[mti++];

    y ^= (y >> 11);
    y ^= (y << 7) & 0x9D2C5680;
    y ^= (y << 15) & 0xEFC60000;
    y ^= (y >> 18);

    return y;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Usage: %s <val1> <val2>\n", argv[0]);
        return 1;
    }

    uint32_t target1 = (uint32_t)strtoul(argv[1], NULL, 10);
    uint32_t target2 = (uint32_t)strtoul(argv[2], NULL, 10);
    
    // Iterate all 32-bit seeds
    // This loops 4 billion times. On modern CPU ~1-2 minutes.
    // Optimization: OpenMP?
    
    #pragma omp parallel for schedule(dynamic)
    for (uint64_t s = 0; s <= 0xFFFFFFFF; s++) {
        // Local state to avoid race conditions if we parallelize
        // But for simplicity, let's keep it creating its own state structure or just use function vars
        // Since the init is expensive, we want to be efficient.
        
        // Actually, declaring large array on stack inside loop might be bad for cache.
        // But `mt` is only 2.5KB.
        
        uint32_t local_mt[N];
        int local_mti = N; // Python starts at N
        
        // Init
        local_mt[0] = (uint32_t)s;
        for (int i = 1; i < N; i++) {
            local_mt[i] = (1812433253UL * (local_mt[i - 1] ^ (local_mt[i - 1] >> 30)) + i);
        }
        
        // We need next_u32() twice
        // 1. Twist
        // The python code calls twist() immediately because index=N
        
        // Twist Logic
        // We can optimize: we only need the first output right now.
        // First output depends on mt[0], mt[1], mt[M]... 
        // Twist updates the whole array.
        
        // Let's just do full twist. It's fast.
        for (int i = 0; i < N; i++) {
            uint32_t y = (local_mt[i] & UPPER_MASK) | (local_mt[(i + 1) % N] & LOWER_MASK);
            local_mt[i] = local_mt[(i + M) % N] ^ (y >> 1) ^ ((y & 1) ? MATRIX_A : 0);
        }
        local_mti = 0;
        
        // Extract 1
        uint32_t y1 = local_mt[local_mti++];
        y1 ^= (y1 >> 11);
        y1 ^= (y1 << 7) & 0x9D2C5680;
        y1 ^= (y1 << 15) & 0xEFC60000;
        y1 ^= (y1 >> 18);
        
        if ((y1 & 0xFFFFF) != target1) continue;
        
        // Extract 2
        uint32_t y2 = local_mt[local_mti++];
        y2 ^= (y2 >> 11);
        y2 ^= (y2 << 7) & 0x9D2C5680;
        y2 ^= (y2 << 15) & 0xEFC60000;
        y2 ^= (y2 >> 18);
        
        if ((y2 & 0xFFFFF) != target2) continue;
        
        printf("%lu\n", s);
        exit(0); // Found it
    }
    
    return 1;
}
