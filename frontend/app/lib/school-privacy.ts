export type SchoolPrivacyConsentValue = { collection: boolean; connection: boolean };
export const emptySchoolPrivacyConsent: SchoolPrivacyConsentValue = { collection: false, connection: false };
export function hasSchoolPrivacyConsent(value: SchoolPrivacyConsentValue) { return value.collection === true && value.connection === true; }
