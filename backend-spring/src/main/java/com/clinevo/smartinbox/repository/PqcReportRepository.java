package com.clinevo.smartinbox.repository;

import com.clinevo.smartinbox.model.PqcReportEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PqcReportRepository extends JpaRepository<PqcReportEntity, Long> {
}
