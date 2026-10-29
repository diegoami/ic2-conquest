#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
/* For each seed: walk the Delphi LCG from RandSeed=seed; for each start offset N, simulate the weather roll
   (20 centres, Random(15)==0, 208 Random(2) ring draws per hit) and report N whose hit mask equals the observed. */
static inline uint32_t nx(uint32_t s){return s*0x08088405u+1u;}
int main(int argc,char**argv){ long M=atol(argv[1]); int seed,mask;
 while(scanf("%d %d",&seed,&mask)==2){ uint32_t s=(uint32_t)seed; int found=0;
  for(long N=0;N<M;N++){ uint32_t t=s; int m=0;
   for(int k=0;k<20;k++){ t=nx(t); if((uint32_t)(((uint64_t)t*15)>>32)==0){ m|=1<<k; for(int j=0;j<208;j++) t=nx(t);} if((m & ~mask)) break; }
   if(m==mask){ printf("seed %d N %ld\n",seed,N); found++; }
   s=nx(s);}
  printf("seed %d mask %d matches %d\n",seed,mask,found); fflush(stdout);} }
