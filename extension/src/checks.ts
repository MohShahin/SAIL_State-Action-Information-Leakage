/**
 * The five leakage checks, in the order they run and are shown. Names and questions are the
 * plain-language wording from the design; `code` matches the category ids sail-leakage reports.
 */
export interface CheckInfo {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly question: string;
}

export const CHECKS: readonly CheckInfo[] = [
  {
    id: 'c1',
    code: 'construction',
    name: 'Construction leakage',
    question: 'Is a treatment dose built into one of the patient-state scores?',
  },
  {
    id: 'c2',
    code: 'reconstruction',
    name: 'Reconstruction leakage',
    question: 'Can a hidden score be rebuilt from the scores the model can see?',
  },
  {
    id: 'c3',
    code: 'temporal_overlap',
    name: 'Temporal overlap',
    question: 'Does the treatment period overlap the time window the state describes?',
  },
  {
    id: 'c4',
    code: 'timing',
    name: 'Timing violation',
    question: 'Is any state value measured after the treatment it should come before?',
  },
  {
    id: 'c5',
    code: 'persistence',
    name: 'Persistence dominance',
    question: 'Would simply repeating the last treatment beat your model?',
  },
];
