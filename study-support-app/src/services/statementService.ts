// Placeholder for Statement API service functions
import { fetchWithAuth } from '@/lib/fetchWithAuth';
import { PersonalStatementResponse, PersonalStatementCreate, PersonalStatementUpdate } from '@/types/personal_statement';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';
const STATEMENTS_API_URL = `${API_BASE_URL}/api/v1/statements`;

// GET /statements/
export const getStatements = async (): Promise<PersonalStatementResponse[]> => {
    console.log(`Fetching statements from: ${STATEMENTS_API_URL}`);
    const response = await fetchWithAuth(STATEMENTS_API_URL);
    if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to fetch statements:', response.status, errorText);
        throw new Error(`Failed to fetch statements: ${response.statusText}`);
    }
    const data = await response.json();
    console.log('Received statements:', data);
    return data;
};

// DELETE /statements/{statement_id}
export const deleteStatement = async (id: string): Promise<void> => {
    const url = `${STATEMENTS_API_URL}/${id}`;
    console.log(`Deleting statement at: ${url}`);
    const response = await fetchWithAuth(url, {
        method: 'DELETE',
    });
    if (!response.ok) {
        // Try to parse error details if possible
        let errorDetail = `Failed to delete statement: ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorDetail;
        } catch (e) { /* Ignore JSON parsing error */ }
        console.error('Failed to delete statement:', response.status, errorDetail);
        throw new Error(errorDetail);
    }
    console.log(`Successfully deleted statement: ${id}`);
    // No return value needed for successful DELETE often (or return response status)
};

// Add placeholder functions for create and update if needed later
// export const createStatement = async (data: PersonalStatementCreate): Promise<PersonalStatementResponse> => { ... };
// export const updateStatement = async (id: string, data: PersonalStatementUpdate): Promise<PersonalStatementResponse> => { ... }; 