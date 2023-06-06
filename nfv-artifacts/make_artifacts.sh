# @Author: Rafael Direito
# @Date:   2022-10-15 21:48:44
# @Last Modified by:   Rafael Direito
# @Last Modified time: 2022-10-15 22:00:01
#!/bin/bash


while test $# -gt 0
do
    case "$1" in
        all) 
            echo "Building all artifacts..."
            mkdir -p outputs
            COPYFILE_DISABLE=true tar -cvf outputs/tunnel_as_a_service_sd_vnf.tar.gz tunnel_as_a_service_sd_vnf
            COPYFILE_DISABLE=true tar -cvf outputs/tunnel_as_a_service_sd_ns.tar.gz tunnel_as_a_service_sd_ns
            cp tunnel_as_a_service_sd_nst.yaml outputs/tunnel_as_a_service_sd_nst.yaml
            ;;
        vnf) echo "Building the VNF..."
            mkdir -p outputs
            COPYFILE_DISABLE=true tar -cvf outputs/tunnel_as_a_service_sd_vnf.tar.gz tunnel_as_a_service_sd_vnf
            ;;
        ns) echo "Building the NS..."
            mkdir -p outputs
            COPYFILE_DISABLE=true tar -cvf outputs/tunnel_as_a_service_sd_ns.tar.gz tunnel_as_a_service_sd_ns
            ;;
        nst) echo "Building the NST..."
            mkdir -p outputs
            cp tunnel_as_a_service_sd_nst.yaml outputs/tunnel_as_a_service_sd_nst.yaml
            ;;
        
    esac
    shift
done

exit 0