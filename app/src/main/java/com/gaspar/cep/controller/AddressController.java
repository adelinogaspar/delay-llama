package com.gaspar.cep.controller;

import com.gaspar.cep.client.CepClient;
import com.gaspar.cep.dto.AddressResponseDto;
import com.gaspar.cep.mapper.CepClientMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/v1/cep")
@RequiredArgsConstructor
public class AddressController {
    private final CepClient cepClient;
    private final CepClientMapper cepClientMapper;

    @GetMapping("/{cep}")
    public AddressResponseDto getCep(@PathVariable String cep ) {
        return cepClientMapper.toAddressResponseDto(cepClient.getCep(cep));
    }
}
