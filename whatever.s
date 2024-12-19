.global _start
.p2align 3

_return_int:
add X0, X0, 2

ret

_start:
    mov X0, 2
    bl _return_int
    cmp X0, 4
    b.eq print_hello_world

    mov     X0, #0     
    mov     X16, #1    
    svc     0           

print_hello_world: mov X0, #1
        adr X1, helloworld
        mov X2, #13
        mov X16, #4 
        svc 0 
        ret

helloworld:      .ascii  "Hello World!\n" // 13