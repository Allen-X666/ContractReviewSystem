package com.example.contractreview;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class ContractReviewApplication {

    public static void main(String[] args) {
        SpringApplication.run(ContractReviewApplication.class, args);
    }

}
