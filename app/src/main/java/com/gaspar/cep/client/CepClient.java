package com.gaspar.cep.client;

import com.gaspar.cep.entity.CepClientEntity;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient( name = "brasil-api", url = "${brasil-api.url}" )
public interface CepClient {
    @GetMapping("/api/cep/v1/{cep}")
    CepClientEntity getCep(@PathVariable("cep") String cep );
}