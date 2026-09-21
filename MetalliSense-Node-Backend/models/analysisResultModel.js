const mongoose = require('mongoose');

/**
 * AnalysisResult — persists every agent analysis produced by /api/v2/ai/agent/analyze.
 *
 * Includes the full ML output so results can be reviewed, trended, and used
 * to build a real-data feedback loop for model retraining.
 */
const analysisResultSchema = new mongoose.Schema(
  {
    // Who triggered this analysis (Firebase UID — null for unauthenticated requests)
    userId: {
      type: String,
      default: null,
      index: true,
    },

    // Input
    metalGrade: {
      type: String,
      required: [true, 'Metal grade is required'],
      uppercase: true,
      trim: true,
      index: true,
    },
    composition: {
      Fe: { type: Number, required: true },
      C: { type: Number, required: true },
      Si: { type: Number, required: true },
      Mn: { type: Number, required: true },
      P: { type: Number, required: true },
      S: { type: Number, required: true },
    },

    // Anomaly agent output
    anomalyScore: { type: Number, default: null },
    anomalySeverity: {
      type: String,
      enum: ['NORMAL', 'LOW', 'MEDIUM', 'HIGH', 'ERROR', 'UNKNOWN'],
      default: 'UNKNOWN',
    },
    anomalyConfidence: { type: Number, default: null },
    anomalyExplanation: { type: String, default: null },

    // Alloy agent output
    recommendedAdditions: {
      type: Map,
      of: Number,
      default: {},
    },
    alloyConfidence: { type: Number, default: null },
    alloyExplanation: { type: String, default: null },
    deviations: {
      type: Map,
      of: Number,
      default: {},
    },

    // Safety note appended by AgentManager
    finalNote: { type: String, default: 'Human approval required before action' },

    // Whether the AI service was reachable at analysis time
    serviceAvailable: { type: Boolean, default: true },

    // -----------------------------------------------------------------------
    // Operator feedback (populated via PATCH /api/v2/ai/results/:id/feedback)
    // -----------------------------------------------------------------------
    operatorConfirmed: {
      type: Boolean,
      default: null, // null = no feedback yet
    },
    operatorNotes: {
      type: String,
      default: null,
    },
    feedbackAt: {
      type: Date,
      default: null,
    },
  },
  {
    timestamps: true,
    toJSON: { virtuals: true },
    toObject: { virtuals: true },
  },
);

// Fast queries for history views and retraining exports
analysisResultSchema.index({ metalGrade: 1, createdAt: -1 });
analysisResultSchema.index({ userId: 1, createdAt: -1 });
analysisResultSchema.index({ anomalySeverity: 1, createdAt: -1 });
analysisResultSchema.index({ operatorConfirmed: 1 });

const AnalysisResult = mongoose.model('AnalysisResult', analysisResultSchema);

module.exports = AnalysisResult;
