package com.gaspar.cep.entity;

import lombok.Data;

@Data
public class CepClientEntity {
    String cep;
    String state;
    String city;
    String neighborhood;
    String street;
    String service;
}
