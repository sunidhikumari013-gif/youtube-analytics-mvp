import type { VideoItem } from '../api/dashboard'

interface TopVideosTableProps {
  videos: VideoItem[]
}

export default function TopVideosTable({ videos }: TopVideosTableProps) {
  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left px-4 py-3 font-semibold text-gray-600">Video</th>
            <th className="text-right px-4 py-3 font-semibold text-gray-600">Views</th>
            <th className="text-right px-4 py-3 font-semibold text-gray-600">Likes</th>
            <th className="text-right px-4 py-3 font-semibold text-gray-600">Comments</th>
            <th className="text-right px-4 py-3 font-semibold text-gray-600">Engagement</th>
          </tr>
        </thead>
        <tbody>
          {videos.map((video, i) => (
            <tr
              key={video.video_id}
              className={i % 2 === 1 ? 'bg-gray-50' : 'bg-white'}
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  {video.thumbnail_url && (
                    <img
                      src={video.thumbnail_url}
                      alt={video.title}
                      className="w-16 h-9 object-cover rounded"
                    />
                  )}
                  <span className="font-medium text-gray-800 line-clamp-2 max-w-xs">
                    {video.title}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {video.views.toLocaleString()}
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {video.likes.toLocaleString()}
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {video.comments.toLocaleString()}
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {video.engagement_rate.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
