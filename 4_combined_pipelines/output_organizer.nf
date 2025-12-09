// Create an output organizer module (module/local/output_organizer.nf)

process OUTPUT_ORGANIZER {
    input:
    path rnasplice_results optional true
    path rnafusion_results optional true
    path sarek_results optional true
    path combined_results optional true

    output:
    path "organized_results"

    script:
    """
    mkdir -p organized_results
    LOG=organized_results/organizer.log // Create log file
    touch $LOG

    # RNASPLICE outputs
    // TODO: Check exact files I need
    // rnasplice
    // $projectDir/star_salmon/suppa/generate_events/per_local_event/events.ioe
    // $projectDir/star_salmon/suppa/diffsplice/per_local_event/$contrast_local_diffsplice.dpsi
    // $projectDir/star_salmon/suppa/diffsplice/per_local_event/$contrast_local_diffsplice.psivec

    // $projectDir/star_salmon/edger/
    // $projectDir/star_salmon/salmon/$sample_id/quant.genes.sf
    // $projectDir/star_salmon/tximport/.txt (especially supa_tpm.txt)

    // $projectDir/star_salmon/rmats/$contrast/rmats_post/.txt

    if [ -d "${rnasplice_results}" ]; then
        if [ -f "${rnasplice_results}/star_salmon/suppa/generate_events/per_local_event/events.ioe" ]; then
            cp ${rnasplice_results}/star_salmon/suppa/generate_events/per_local_event/events.ioe organized_results/rnasplice_generateEvents
            echo "Copied rnasplice SUPPA generateEvents" >> $LOG
        else
            echo "Missing rnasplice SUPPA generateEvents" >> $LOG
        fi

        if [ -d "${rnasplice_results}" ]; then
        if [ -f "${rnasplice_results}/star_salmon/suppa/diffsplice/per_local_event/$contrast_local_diffsplice.*" ]; then
            cp ${rnasplice_results}/star_salmon/suppa/diffsplice/per_local_event/$contrast_local_diffsplice.* organized_results/rnasplice_diffsplice_dpsi
            echo "Copied rnasplice SUPPA diffsplice" >> $LOG
        else
            echo "Missing rnasplice SUPPA diffsplice" >> $LOG
        fi

        if [ -d "${rnasplice_results}" ]; then
        if [ -f "${rnasplice_results}/star_salmon/edger/" ]; then
            cp ${rnasplice_results}/star_salmon/edger/ organized_results/rnasplice_edger
            echo "Copied rnasplice SUPPA edger" >> $LOG
        else
            echo "Missing rnasplice SUPPA edger" >> $LOG
        fi
        if [ -d "${rnasplice_results}/star_salmon/tximport/suppa_tpm.txt" ]; then
            cp -r ${rnasplice_results}/star_salmon/tximport/suppa_tpm.txt organized_results/rnasplice_tximport
            echo "Copied rnasplice tximport suppa_tpm.txt" >> $LOG
        else
            echo "Missing rnasplice tximport suppa_tpm.txt" >> $LOG
        fi

        if [ -d "${rnasplice_results}/star_salmon/rmats/$contrast/rmats_post/*.txt" ]; then
            cp -r ${rnasplice_results}/star_salmon/rmats/$contrast/rmats_post/*.txt organized_results/rnasplice_rMATS
            echo "Copied rnasplice rMATS directory" >> $LOG
        else
            echo "Missing rnasplice rMATS directory" >> $LOG
        fi

        if [ -d "${rnasplice_results}/star_salmon/salmon/$sample_id/quant.genes.sf" ]; then
            cp -r ${rnasplice_results}/star_salmon/salmon/$sample_id/quant.genes.sf organized_results/rnasplice_salmon
            echo "Copied rnasplice salmon quant.genes.sf" >> $LOG
        else
            echo "Missing rnasplice salmon quant.genes.sf" >> $LOG
        fi
           
    else
        echo "rnasplice results not found" >> $LOG
    fi

    # RNAFUSION outputs
    // TODO: Check exact files I need
    // rnafusion
    // $projectDir/arriba/$sample_id.arriba.fusions.tsv
    // $projectDir/fusioncatcher/$sample_id.fusioncatcher.fusion-genes.txt
    // $projectDir/fusioninspector/$sample_id.FusionInspector.fusions.tsv
    // $projectDir/fusionreport/$sample_id/$sample_id.fusionreport_filtered.tsv
    // $projectDir/starfusion/$sample_id.starfusion.fusion_predictions.tsv
    // $projectDir/vcf/$sample_id.fusion_data.vcf.gz
    // $projectDir/stringtie/$sample_id.gene.abundance.txt
    // $projectDir/stringtie/$sample_id.transcripts.gtf

    if [ -d "${rnafusion_results}" ]; then
        if [ -f "${rnafusion_results}/arriba/$sample_id.arriba.fusions.tsv" ]; then
            cp -r ${rnafusion_results}/arriba/$sample_id.arriba.fusions.tsv organized_results/rnafusion_arriba
            echo "Copied rnafusion arriba directory" >> $LOG
        else
            echo "Missing rnafusion arriba directory" >> $LOG
        fi
        if ls ${rnafusion_results}/fusioncatcher/$sample_id.fusioncatcher.fusion-genes.txt 1> /dev/null 2>&1; then
            mkdir -p organized_results/rnafusion_fusioncatcher
            cp ${rnafusion_results}/fusioncatcher/$sample_id.fusioncatcher.fusion-genes.txt organized_results/rnafusion_fusioncatcher/
            echo "Copied rnafusion fusioncatcher fusioncatcher.fusion-genes.txt files" >> $LOG
        else
            echo "Missing rnafusion fusioncatcher fusioncatcher.fusion-genes.txt files" >> $LOG
        fi
        if ls ${rnafusion_results}/fusioninspector/$sample_id.FusionInspector.fusions.tsv 1> /dev/null 2>&1; then
            mkdir -p organized_results/rnafusion_fusioninspector
            cp ${rnafusion_results}/fusioninspector/$sample_id.FusionInspector.fusions.tsv organized_results/rnafusion_fusioninspector/
            echo "Copied rnafusion fusioninspector FusionInspector.fusions.tsv files" >> $LOG
        else
            echo "Missing rnafusion fusioninspector FusionInspector.fusions.tsv files" >> $LOG
        fi
        if ls ${rnafusion_results}/fusionreport/$sample_id/$sample_id.fusionreport_filtered.tsv /dev/null 2>&1; then
            mkdir -p organized_results/rnafusion_fusionreport
            cp ${rnafusion_results}/fusionreport/$sample_id/$sample_id.fusionreport_filtered.tsv organized_results/rnafusion_fusionreport/
            echo "Copied rnafusion fusionreport fusionreport_filtered.tsv files" >> $LOG
        else
            echo "Missing rnafusion fusionreport fusionreport_filtered.tsv files" >> $LOG
        fi
        if ls ${rnafusion_results}/starfusion/$sample_id.starfusion.fusion_predictions.tsv 1> /dev/null 2>&1; then
            mkdir -p organized_results/rnafusion_starfusion
            cp ${rnafusion_results}/starfusion/$sample_id.starfusion.fusion_predictions.tsv organized_results/rnafusion_starfusion/
            echo "Copied rnafusion starfusion fusion_predictions.tsv files" >> $LOG
        else
            echo "Missing rnafusion starfusion fusion_predictions.tsv files" >> $LOG
        fi

        if ls ${rnafusion_results}/vcf/$sample_id.fusion_data.vcf.gz 1> /dev/null 2>&1; then
            mkdir -p organized_results/rnafusion_vcf
            cp ${rnafusion_results}/vcf/$sample_id.fusion_data.vcf.gz organized_results/rnafusion_vcf/
            echo "Copied rnafusion vcf fusion_data.vcf.gz files" >> $LOG
        else
            echo "Missing rnafusion vcf fusion_data.vcf.gz files" >> $LOG
        fi
        if ls ${rnafusion_results}/stringtie/$sample_id.gene.abundance.txt 1> /dev/null 2>&1; then
            mkdir -p organized_results/rnafusion_stringtie
            cp ${rnafusion_results}/stringtie/$sample_id.gene.abundance.txt organized_results/rnafusion_stringtie/
            echo "Copied rnafusion stringtie gene.abundance.txt files" >> $LOG
        else
            echo "Missing rnafusion stringtie gene.abundance.txt files" >> $LOG
        fi

    else
        echo "rnafusion results not found" >> $LOG
    fi

    # SAREK outputs
    // TODO: Check exact files I need
    // sarek
    // $projectDir/annotation/$variant_caller/$sample_id.$variant_caller.ann.vcf.gz
    // $projectDir/variant_calling/$variant_caller/$sample_id.$variant_caller.vcf.gz

    if [ -d "${sarek_results}" ]; then
        if ls ${sarek_results}/variant_calling/*.vcf.gz* 1> /dev/null 2>&1; then
            mkdir -p organized_results/sarek_variant_calling
            cp ${sarek_results}/variant_calling/*.vcf.gz* organized_results/sarek_variant_calling/
            echo "Copied sarek variant_calling .vcf.gz and .vcf.gz.tbifiles" >> $LOG
        else
            echo "Missing sarek variant_calling .vcf.gz and .vcf.gz.tbi files" >> $LOG
        fi
        if ls ${sarek_results}/annotation/*.vcf.gz* 1> /dev/null 2>&1; then
            mkdir -p organized_results/sarek_annotation
            cp ${sarek_results}/annotation/*.vcf.gz* organized_results/sarek_annotation/
            echo "Copied sarek annotation .vcf.gz files" >> $LOG
        else
            echo "Missing sarek annotation .vcf.gz and .vcf.gz.tbi files" >> $LOG
        fi
    else
        echo "sarek results not found" >> $LOG
    fi

    # Fail if compulsory outputs are missing
    missing=0
    if ! [ -f organized_results/rnasplice_generateEvents ]; then missing=1; fi
    if ! [ -d organized_results/rnafusion_arriba ]; then missing=1; fi
    if ! ls organized_results/sarek_variant_calling/*.vcf 1> /dev/null 2>&1; then missing=1; fi
    if [ "$missing" -eq 1 ]; then
        echo "ERROR: One or more compulsory outputs are missing. See $LOG for details." >> $LOG
        exit 1
    fi
    """
}





