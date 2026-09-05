package com.clinevo.smartinbox.repository;

import com.clinevo.smartinbox.model.IcsrReportEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface IcsrReportRepository extends JpaRepository<IcsrReportEntity, Long> {
}
