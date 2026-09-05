package com.clinevo.smartinbox.ingestion;

import java.util.List;

public interface IngestionSource {
    List<RawEmailPayload> fetchNewEmails() throws Exception;
    String getSourceName();
}
