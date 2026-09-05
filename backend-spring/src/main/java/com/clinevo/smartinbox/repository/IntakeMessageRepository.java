package com.clinevo.smartinbox.repository;

import com.clinevo.smartinbox.model.IntakeMessageEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface IntakeMessageRepository extends JpaRepository<IntakeMessageEntity, Long> {
    Optional<IntakeMessageEntity> findByMessageId(String messageId);
    List<IntakeMessageEntity> findByStatusOrderByCreatedAtDesc(String status);
    List<IntakeMessageEntity> findAllByOrderByCreatedAtDesc();
    boolean existsByMessageId(String messageId);
}
