bits = [0,0,0,1,0,1]


res=0
ll=len(bits)
for i in range(ll):
    res+=bits[ll-i-1]<<i
print(res)