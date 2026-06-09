package com.gaspar.cep.dto;

import lombok.Data;

@Data
public class AddressResponseDto {
    String cep;
    String state;
    String city;
    String neighborhood;
    String street;
}
