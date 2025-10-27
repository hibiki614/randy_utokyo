from glob import glob
import pandas as pd

links=['533967_00940_13718_0','I_11_533967_13718533967_00977','533967_00939_01421_1','I_11_533967_00977533967_01421','I_11_533967_00977533967_01555','533967_01555_14156_0','533967_00766_14156_1','I_11_533967_01555533967_00977','533967_01555_14156_1','533967_00766_14156_0','533967_00766_11513_0','533967_00538_11513_1','533967_00766_11513_1','533967_00538_11513_0']

segments=[['06','0600-0700'],['07','0700-0800'],['08','0800-0900'],['09','0900-1000'],['10','1000-1100'],['11','1100-1200'],['12','1200-1300'],['13','1300-1400'],['14','1400-1500'],['15','1500-1600'],['16','1600-1700'],['17','1700-1800'],['18','1800-1900']]

def filter_content(name):
	df=pd.read_csv(name).filter(items=["Time","VID","Type","Pos.x","Pos.y","LinkID"])
	df=df[df.LinkID.apply(lambda x: x in links)].filter(items=["Time","VID","Type","Pos.x","Pos.y"])
	for hour, segment in segments:
		df[df.Time.apply(lambda x: str(x)[:2]==hour)].to_csv(name.replace('.csv','_'+segment+'.csv'))

def select_file(s=''):
    filenames=glob('vpos*'+s+'*_ext.csv')
    print('\nSelect files\n'+'\n'.join(['\t'+str(k)+' : '+fn for k,fn in enumerate(filenames)])+'\n')
    selection=[filenames[i] for i in range(int(input('From = ')),int(input('To = '))+1)]
    for name in selection:
        filter_content(name)

select_file()