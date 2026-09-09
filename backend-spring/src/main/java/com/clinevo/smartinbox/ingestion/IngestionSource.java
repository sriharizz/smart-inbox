package com.clinevo.smartinbox.ingestion;

import java.util.List;

public interface IngestionSource {
    List<RawEmailPayload> fetchNewEmails() throws Exception;

    default List<RawEmailPayload> fetchNewEmails(java.util.function.Predicate<String> isAlreadyIngested) throws Exception {
        return fetchNewEmails();
    }

    String getSourceName();
}
