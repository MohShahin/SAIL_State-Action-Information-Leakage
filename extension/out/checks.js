"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CHECKS = void 0;
exports.CHECKS = [
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
//# sourceMappingURL=checks.js.map