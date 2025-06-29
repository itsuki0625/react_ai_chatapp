// Placeholder for Statement API service functions
import { PersonalStatementResponse } from '@/types/personal_statement';
import { apiClient } from '@/lib/api';
// import { PersonalStatementCreate, PersonalStatementUpdate } from '@/types/personal_statement';

// GET /statements/
export const getStatements = async (): Promise<PersonalStatementResponse[]> => {
    try {
        console.log('Fetching statements from API');
        const response = await apiClient.get('/api/v1/statements/');
        console.log('Received statements:', response.data);
        return response.data;
    } catch (error) {
        console.error('Failed to fetch statements:', error);
        throw error;
    }
};

// DELETE /statements/{statement_id}
export const deleteStatement = async (id: string): Promise<void> => {
    try {
        console.log(`Deleting statement: ${id}`);
        await apiClient.delete(`/api/v1/statements/${id}/`);
        console.log(`Successfully deleted statement: ${id}`);
    } catch (error) {
        console.error('Failed to delete statement:', error);
        throw error;
    }
};

// Add placeholder functions for create and update if needed later
// export const createStatement = async (data: PersonalStatementCreate): Promise<PersonalStatementResponse> => { ... };
// export const updateStatement = async (id: string, data: PersonalStatementUpdate): Promise<PersonalStatementResponse> => { ... }; 