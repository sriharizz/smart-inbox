package com.clinevo.smartinbox;

import com.clinevo.smartinbox.model.AuditEventEntity;
import com.clinevo.smartinbox.service.AuditService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@TestPropertySource(properties = {
    "smartinbox.ingestion.auto-ingest-on-startup=false"
})
class AuditServiceTest {

    @Autowired
    private AuditService auditService;

    @Test
    void testAuditLogEventCreationAndQuery() {
        Long testMessageId = 999L;
        AuditEventEntity event = auditService.logEvent(
                testMessageId,
                "dr.reviewer@clinevo.com",
                "OVERRIDE_CATEGORY",
                "PRIMARY_CATEGORY",
                "Safety Report (ICSR)",
                "Quality Complaint (PQC)",
                "Vial particulate confirmed under human review."
        );

        assertNotNull(event);
        assertNotNull(event.getId());
        assertTrue(event.getIsImmutable());
        assertEquals("OVERRIDE_CATEGORY", event.getAction());
        assertEquals("PRIMARY_CATEGORY", event.getTargetField());

        List<AuditEventEntity> trail = auditService.getAuditTrail(testMessageId);
        assertFalse(trail.isEmpty());
        assertEquals(event.getId(), trail.get(0).getId());
    }
}
