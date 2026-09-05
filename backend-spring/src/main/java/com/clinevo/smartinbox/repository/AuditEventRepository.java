package com.clinevo.smartinbox.repository;

import com.clinevo.smartinbox.model.AuditEventEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface AuditEventRepository extends JpaRepository<AuditEventEntity, Long> {
    List<AuditEventEntity> findByMessageIdOrderByTimestampDesc(Long messageId);
    List<AuditEventEntity> findAllByOrderByTimestampDesc();
}
