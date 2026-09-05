package com.clinevo.smartinbox.repository;

import com.clinevo.smartinbox.model.MedicalInfoEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface MedicalInfoRepository extends JpaRepository<MedicalInfoEntity, Long> {
}
