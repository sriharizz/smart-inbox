package com.clinevo.smartinbox;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(properties = {
    "smartinbox.ingestion.auto-ingest-on-startup=false"
})
class SmartInboxApplicationTests {

    @Test
    void contextLoads() {
    }
}
