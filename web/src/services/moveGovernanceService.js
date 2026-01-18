import api from './api';

const moveGovernanceService = {
    /**
     * Transfer flat dues to a personal arrears ledger
     * @param {Object} data { member_id, flat_id, amount, notes }
     */
    transferToArrears: async (data) => {
        const response = await api.post('/move-governance/transfer-to-arrears', data);
        return response.data;
    },

    /**
     * List all personal arrears
     */
    listPersonalArrears: async () => {
        const response = await api.get('/move-governance/personal-arrears');
        return response.data;
    },

    /**
     * Download No Dues Certificate (NDC)
     * @param {number} flatId 
     */
    downloadNDC: async (flatId, flatNumber) => {
        const response = await api.get(`/move-governance/generate-ndc/${flatId}`, {
            responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `NDC_${flatNumber}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    },

    /**
     * Download Police Verification Form for a member
     * @param {number} memberId 
     * @param {string} memberName 
     */
    downloadPoliceVerification: async (memberId, memberName) => {
        const response = await api.get(`/move-governance/police-verification-form/${memberId}`, {
            responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Police_Verification_${memberName}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    },

    /**
     * Calculate final bill for move-out
     * @param {number} flatId 
     */
    calculateFinalBill: async (flatId) => {
        const response = await api.get(`/move-governance/calculate-final-bill/${flatId}`);
        return response.data;
    },

    /**
     * Raise an instant damage/misuse claim
     * @param {Object} data { flat_id, amount, description, instant_post }
     */
    raiseDamageClaim: async (data) => {
        const response = await api.post('/move-governance/damage-claim', data);
        return response.data;
    }
};

export default moveGovernanceService;
