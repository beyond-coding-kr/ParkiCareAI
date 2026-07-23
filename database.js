const { Sequelize, DataTypes } = require('sequelize');
const path = require('path');

const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: path.join(__dirname, 'parkicare.db'),
  logging: false
});

const User = sequelize.define('User', {
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  username: { type: DataTypes.STRING(50), unique: true, allowNull: false },
  password_hash: { type: DataTypes.STRING(256), allowNull: false },
  created_at: { type: DataTypes.DATE, defaultValue: Sequelize.NOW }
}, { tableName: 'users', timestamps: false });

const Profile = sequelize.define('Profile', {
  id: { type: DataTypes.STRING(64), primaryKey: true },
  name: { type: DataTypes.STRING(100), allowNull: false },
  age: { type: DataTypes.INTEGER, allowNull: false },
  created_at: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
  user_id: { type: DataTypes.INTEGER, references: { model: User, key: 'id' } }
}, { tableName: 'profiles', timestamps: false });

const GameSession = sequelize.define('GameSession', {
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  profile_id: { type: DataTypes.STRING(64), allowNull: false, references: { model: Profile, key: 'id' } },
  game_type: { type: DataTypes.STRING(50), allowNull: false },
  accuracy: { type: DataTypes.FLOAT, allowNull: false },
  avg_response_time: { type: DataTypes.FLOAT, allowNull: false },
  correct_count: { type: DataTypes.INTEGER, allowNull: false },
  total_rounds: { type: DataTypes.INTEGER, allowNull: false },
  difficulty: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 2 },
  timestamp: { type: DataTypes.DATE, defaultValue: Sequelize.NOW }
}, { tableName: 'game_sessions', timestamps: false });

const GlobalStats = sequelize.define('GlobalStats', {
  game_type: { type: DataTypes.STRING(50), primaryKey: true },
  avg_response_time: { type: DataTypes.FLOAT, allowNull: false, defaultValue: 2000.0 },
  count: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 }
}, { tableName: 'global_stats', timestamps: false });

const WeakProfile = sequelize.define('WeakProfile', {
  profile_id: { type: DataTypes.STRING(64), primaryKey: true, references: { model: Profile, key: 'id' } },
  data_json: { type: DataTypes.TEXT, allowNull: false },
  updated_at: { type: DataTypes.DATE, defaultValue: Sequelize.NOW }
}, { tableName: 'weak_profiles', timestamps: false });

// Relationships
User.hasMany(Profile, { foreignKey: 'user_id' });
Profile.belongsTo(User, { foreignKey: 'user_id' });

Profile.hasMany(GameSession, { foreignKey: 'profile_id' });
GameSession.belongsTo(Profile, { foreignKey: 'profile_id' });

Profile.hasOne(WeakProfile, { foreignKey: 'profile_id' });
WeakProfile.belongsTo(Profile, { foreignKey: 'profile_id' });

module.exports = {
  sequelize,
  User,
  Profile,
  GameSession,
  GlobalStats,
  WeakProfile
};
