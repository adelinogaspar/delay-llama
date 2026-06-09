package com.gaspar.cep.mapper;

import com.gaspar.cep.client.CepClient;
import com.gaspar.cep.dto.AddressResponseDto;
import com.gaspar.cep.entity.CepClientEntity;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface CepClientMapper {
    AddressResponseDto toAddressResponseDto(CepClientEntity cepClientEntity);
}
