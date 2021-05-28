#define N 10

int main() {
    volatile unsigned * result = (unsigned*) 2048;

    if(N < 2)
        *result = N;
    else {
        int a = 0;
        int b = 1;
        int c = a + b;
        for(int i = 2; i < N; i++) {
            a = b;
            b = c;
            c = a + b;
        }
        *result = c;
    }

    while (1);
}