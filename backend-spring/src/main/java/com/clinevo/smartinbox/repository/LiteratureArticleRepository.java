package com.clinevo.smartinbox.repository;

import com.clinevo.smartinbox.model.LiteratureArticleEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface LiteratureArticleRepository extends JpaRepository<LiteratureArticleEntity, Long> {
    List<LiteratureArticleEntity> findAllByOrderByCreatedAtDesc();
}
