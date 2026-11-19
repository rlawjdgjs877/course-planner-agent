import assert from 'node:assert/strict';
import { hasSchoolPrivacyConsent } from '../app/lib/school-privacy.ts';
assert.equal(hasSchoolPrivacyConsent({collection:false,connection:false}),false);
assert.equal(hasSchoolPrivacyConsent({collection:true,connection:false}),false);
assert.equal(hasSchoolPrivacyConsent({collection:false,connection:true}),false);
assert.equal(hasSchoolPrivacyConsent({collection:true,connection:true}),true);
console.log('PASS: both required consents are necessary; partial or absent consent cannot open the school session.');
