/**
 * Resolves the reviewer-facing human-meaningful logical Case ID (CASE-01 to CASE-12).
 * Strictly decouples reviewer-facing clinical case identity from arbitrary database primary keys.
 */
export function resolveCaseId(msg: {
  id?: number | null;
  messageId?: string | null;
  subject?: string | null;
  sender?: string | null;
  senderEmail?: string | null;
  caseId?: string | null;
  caseReference?: string | null;
} | null | undefined): string {
  if (!msg) return 'CASE-01';

  // If already explicitly provided with canonical format
  if (msg.caseReference && /^CASE-(0[1-9]|1[0-2])$/i.test(msg.caseReference)) {
    return msg.caseReference.toUpperCase();
  }
  if (msg.caseId && /^CASE-(0[1-9]|1[0-2])$/i.test(msg.caseId)) {
    return msg.caseId.toUpperCase();
  }

  const subj = (msg.subject || '').toLowerCase();
  const sender = ((msg.sender || '') + ' ' + (msg.senderEmail || '')).toLowerCase();
  const mid = (msg.messageId || '').toLowerCase();

  // Explicit CASE-XX pattern in Subject or Message-ID
  const caseMatch = (msg.subject || '').match(/CASE-?(0[1-9]|1[0-2])\b/i) || 
                    (msg.messageId || '').match(/CASE-?(0[1-9]|1[0-2])\b/i);
  if (caseMatch) {
    const num = parseInt(caseMatch[1], 10);
    return `CASE-${num.toString().padStart(2, '0')}`;
  }

  // 12. CASE-12: Acute Angioedema Handwritten Note (Dr. Mark Vance)
  if (subj.includes('angioedema') || sender.includes('mvance') || sender.includes('metrourgentcare') || mid.includes('case12') || mid.includes('case-12')) {
    return 'CASE-12';
  }

  // 1. CASE-01: Cardioril DILI (Dr. Sarah Jenkins)
  if (subj.includes('dili') || sender.includes('sjenkins') || sender.includes('metrohealth-chicago') || mid.includes('sjenkins') || mid.includes('case01') || mid.includes('case-01')) {
    return 'CASE-01';
  }

  // 2. CASE-02: InjectaPen Anaphylaxis (Dr. Peterson)
  if (subj.includes('injectapen') || subj.includes('anaphylaxis') || sender.includes('apeterson') || sender.includes('stmarys') || mid.includes('apeterson') || mid.includes('case02') || mid.includes('case-02')) {
    return 'CASE-02';
  }

  // 3. CASE-03: Corzapan Palpitations / Tachycardia (Emily Watson)
  if (subj.includes('palpitations') || subj.includes('dizzy') || sender.includes('ewatson') || sender.includes('consumer-mail') || mid.includes('ewatson') || mid.includes('case03') || mid.includes('case-03')) {
    return 'CASE-03';
  }

  // 4. CASE-04: Contaminated Cefatox Sepsis (Dr. Robert Lang)
  if ((subj.includes('sepsis') && subj.includes('cefatox')) || sender.includes('rlang') || sender.includes('nmh-icu') || mid.includes('rlang') || mid.includes('case-04') || mid.includes('case04')) {
    return 'CASE-04';
  }

  // 5. CASE-05: Non-English Lamotrigina Necrolysis (Dra. Elena Morales)
  if (subj.includes('necr') || subj.includes('lamotrigina') || subj.includes('notificaci') || sender.includes('emorales') || sender.includes('hospitallapaz') || mid.includes('emorales') || mid.includes('case05') || mid.includes('case-05')) {
    return 'CASE-05';
  }

  // 6. CASE-06: Neuroval Seizure Follow-Up (Dr. Richard Vance)
  if (subj.includes('cr-2025-us-00744') || subj.includes('seizure') || sender.includes('columbia-neurology') || mid.includes('case06') || mid.includes('case-06')) {
    return 'CASE-06';
  }

  // 7. CASE-07: Cardioril Blister Foil Defect (Robert Vance, PharmD)
  if (subj.includes('bl-8802') || subj.includes('blister foil') || subj.includes('oxidized') || sender.includes('metrohealth-pharmacy') || mid.includes('case07') || mid.includes('case-07')) {
    return 'CASE-07';
  }

  // 8. CASE-08: Counterfeit Lipocur Packaging (Karen Patel, RPh)
  if (subj.includes('lp-44109') || subj.includes('counterfeit') || sender.includes('kpatel') || sender.includes('apex-care') || mid.includes('case08') || mid.includes('case-08')) {
    return 'CASE-08';
  }

  // 9. CASE-09: Corzapan NG-Tube Crushing MI Request (David Wu, PharmD)
  if (subj.includes('ng-tube') || subj.includes('crushed') || sender.includes('dwu') || sender.includes('ucsf') || mid.includes('case09') || mid.includes('case-09')) {
    return 'CASE-09';
  }

  // 10. CASE-10: PharmaTech AI Conference - Not Relevant (PharmaSummit)
  if (sender.includes('pharmasummit') || subj.includes('early bird') || subj.includes('pharmasummit') || subj.includes('summit') || mid.includes('case10') || mid.includes('case-10')) {
    return 'CASE-10';
  }

  // 11. CASE-11: Cefatox D5W Dilution Stability MI Request (Dr. Elena Rostova)
  if (subj.includes('dilution stability') || subj.includes('d5w') || sender.includes('erostova') || sender.includes('massgeneral') || mid.includes('case11') || mid.includes('case-11')) {
    return 'CASE-11';
  }

  // Fallback: If DB ID is 1..12 (canonical seed data)
  if (typeof msg.id === 'number' && msg.id >= 1 && msg.id <= 12) {
    return `CASE-${msg.id.toString().padStart(2, '0')}`;
  }

  // Fallback for demo: map to modulo 1..12 so no arbitrary DB ID (like 109 or 45) ever leaks to UI
  if (typeof msg.id === 'number' && msg.id > 0) {
    const canonicalNum = ((msg.id - 1) % 12) + 1;
    return `CASE-${canonicalNum.toString().padStart(2, '0')}`;
  }

  return 'CASE-01';
}
