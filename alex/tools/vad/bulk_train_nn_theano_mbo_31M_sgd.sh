#!/bin/sh
## Fail: python.sh
#

DEV='gpu0'
EP='1000'
MF='31000000'
MFS='31M'

BS='1000'
BSS='1k'

PF=15
NF=15

HU=512
HL=1
HLA=3

M='sg-fixedlr'
A='tanh'

export THEANO_FLAGS=mode=FAST_RUN,device=$DEV,floatX=float32
nohup ./train_voip_nn_theano_sds_mfcc.py --max_epoch $EP --method $M --hact $A --batch_size $BS --max_frames $MF --hidden_units $HU --hidden_layers $HL --hidden_layers_add $HLA --prev_frames $PF --next_frames $NF --mel_banks_only 1 > log.nnt_mf_$MFS.hu_$HU.hl_$HL.hla_$HLA.pf_$PF.nf_$NF.mbo.bs_$BSS.$M.$A &


