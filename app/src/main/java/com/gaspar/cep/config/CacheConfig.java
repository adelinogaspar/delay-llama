package com.gaspar.cep.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.TimeUnit;

@Configuration
@EnableCaching
public class CacheConfig {

    @Value("${app.cache.cacheTtlInMinutes:5}")
    private int cacheTtlInMinutes;

    @Bean
    public CacheManager cacheManager() {

        CaffeineCacheManager cacheManager = new CaffeineCacheManager("addressCache");
        cacheManager.setCaffeine(Caffeine.newBuilder()
                .expireAfterWrite(cacheTtlInMinutes, TimeUnit.MINUTES)
                .maximumSize(1000));   // optional: limit number of entries
        return cacheManager;
    }
}
