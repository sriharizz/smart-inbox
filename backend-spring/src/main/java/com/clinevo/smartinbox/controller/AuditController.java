package com.clinevo.smartinbox.controller;

import com.clinevo.smartinbox.model.AuditEventEntity;
import com.clinevo.smartinbox.service.AuditService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/audit-log")
public class AuditController {

    private final AuditService auditService;

    public AuditController(AuditService auditService) {
        this.auditService = auditService;
    }

    @GetMapping
    public List<AuditEventEntity> getAllAuditEvents(@RequestParam(required = false) Long messageId) {
        if (messageId != null) {
            return auditService.getAuditTrail(messageId);
        }
        return auditService.getAllAuditEvents();
    }
}
