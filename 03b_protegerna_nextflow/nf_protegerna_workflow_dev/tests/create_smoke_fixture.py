"""Create a tiny, deterministic two-gene integration fixture (not biological validation)."""
from pathlib import Path
import csv

def create(root):
    root.mkdir(parents=True, exist_ok=True)
    (root/'genome.fa.fai').unlink(missing_ok=True)
    codons = dict(zip('ACDEFGHIKLMNPQRSTVWY', ['GCT','TGT','GAT','GAA','TTT','GGT','CAT','ATT','AAA','CTG','ATG','AAT','CCT','CAA','CGT','TCT','ACT','GTT','TGG','TAT']))
    exons = [('MPEPTIDEKALVAGHIKAAS', 'GGGQTPRKKA', 'VLGHPEPTIDEKAAAVVVKR'),
             ('MALWPEPTIDEKALVGHIAA', 'AAGGQTPRKA', 'WQSTPEPTIDEKGGGVVVKR')]
    genome = list('N'*1000)
    gtf, translations, canonical = [], [], []
    for index, peptides in enumerate(exons,1):
        offset=(index-1)*400
        gene=f'ENSG{index:011d}'
        tx=f'ENST{index:011d}'
        lengths=[len(s)*3 for s in peptides]
        intervals=[(offset+1,offset+lengths[0]),(offset+101,offset+100+lengths[1]),(offset+201,offset+200+lengths[2])]
        for (start,end),peptide in zip(intervals,peptides):
            genome[start-1:end]=''.join(codons[aa] for aa in peptide)
        end=intervals[-1][1]
        genome[end:end+3]='TAA'
        base=f'gene_id "{gene}"; gene_name "GENE{index}"; gene_type "protein_coding";'
        def feature(kind,start,stop,attributes,phase='.'):
            gtf.append(f'chr1\tsmoke\t{kind}\t{start}\t{stop}\t.\t+\t{phase}\t{attributes}')
        feature('gene',offset+1,end+3,base)
        choices=[(tx,intervals,peptides)]
        if index==1:
            choices.append(('ENST00000000003',[intervals[0],intervals[2]],[peptides[0],peptides[2]]))
        for transcript,segments,aa in choices:
            attrs=base+f' transcript_id "{transcript}"; transcript_type "protein_coding";'
            feature('transcript',offset+1,end+3,attrs)
            for i,(start,stop) in enumerate(segments,1):
                feature('exon',start,stop+3 if i==len(segments) else stop,attrs+f' exon_number "{i}";')
                feature('CDS',start,stop,attrs,'0')
            feature('start_codon',offset+1,offset+3,attrs,'0')
            feature('stop_codon',end+1,end+3,attrs,'0')
            translations.append(f'>{transcript}\n'+''.join(aa)+'\n')
        canonical.append(f'>sp|SMOKE{index}|GENE{index}_HUMAN\n'+''.join(peptides)+'\n')
    # Exercise the mandatory negative-strand / partial-CDS / nonzero-phase strata.
    partial='MPEPTIDEKALVAGHIK'
    raw='A'+''.join(codons[aa] for aa in partial)
    reverse=raw.translate(str.maketrans('ACGT','TGCA'))[::-1]
    genome[800:800+len(reverse)]=reverse
    attrs='gene_id "ENSG00000000004"; gene_name "PARTIAL"; transcript_id "ENST00000000004"; transcript_type "protein_coding"; tag "cds_start_NF";'
    for kind in ('gene','transcript','exon','CDS'):
        phase='1' if kind=='CDS' else '.'
        gtf.append(f'chr1\tsmoke\t{kind}\t801\t{800+len(raw)}\t.\t-\t{phase}\t{attrs}')
    translations.append(f'>ENST00000000004\n{partial}\n')
    (root/'genome.fa').write_text('>chr1\n'+''.join(genome)+'\n')
    (root/'annotation.gtf').write_text('\n'.join(gtf)+'\n')
    (root/'gencode.fa').write_text(''.join(translations))
    (root/'reference.fa').write_text(''.join(canonical))
    upstream=len(exons[0][0])*3
    middle_end=100+len(exons[0][1])*3
    downstream_end=200+len(exons[0][2])*3+3
    event=f'ENSG00000000001;SE:chr1:{upstream}-101:{middle_end}-201:+'
    (root/'events.ioe').write_text('seqname\tgene_id\tevent_id\talternative_transcripts\ttotal_transcripts\n'+f'chr1\tENSG00000000001\t{event}\tENST00000000001\tENST00000000001,ENST00000000003\n')
    (root/'events.psi').write_text(f'\tS1\tS2\tS3\n{event}\t0.5\t0.6\t0.7\n')
    fields=['ID','GeneID','geneSymbol','chr','strand','exonStart_0base','exonEnd','upstreamES','upstreamEE','downstreamES','downstreamEE','IJC_SAMPLE_1','SJC_SAMPLE_1','IJC_SAMPLE_2','SJC_SAMPLE_2','IncFormLen','SkipFormLen','PValue','FDR','IncLevel1','IncLevel2','IncLevelDifference']
    row=['1','ENSG00000000001','GENE1','chr1','+',100,middle_end,0,upstream,200,downstream_end,'20,25','10,15','15,20','20,25',150,100,0.001,0.01,'0.7,0.8','0.4,0.5',0.3]
    with (root/'SE.MATS.JC.txt').open('w',newline='') as handle:
        writer=csv.writer(handle,delimiter='\t',lineterminator='\n');writer.writerow(fields);writer.writerow(row)
    (root/'S1.FusionInspector.fusions.abridged.tsv').write_text('#FusionName\tJunctionReadCount\tSpanningFragCount\tLeftGene\tLeftBreakpoint\tRightGene\tRightBreakpoint\tSpliceType\tLargeAnchorSupport\n'+f'GENE1--GENE2\t20\t10\tGENE1^ENSG00000000001\tchr1:{upstream}:+\tGENE2^ENSG00000000002\tchr1:601:+\tONLY_REF_SPLICE\tYES\n')
    (root/'samplesheet.csv').write_text('sample,tool,event_type,path,batch,condition\nS1,fusion,FUSION,S1.FusionInspector.fusions.abridged.tsv,batch1,CASE\nCASE-CTRL,rmats,SE,SE.MATS.JC.txt,batch1,CASE-CTRL\ncohort,suppa,IOE,events.ioe,batch1,NA\ncohort,suppa,PSI,events.psi,batch1,NA\n')

if __name__=='__main__':
    create(Path(__file__).parent/'data/smoke')
