require 'date'

class ChangingLivesOverLimit < Scout::Plugin
  def build_report

    log_file_path = '/var/log/changing-lives.log'
    count = 0

    # Get today's date.
    today = DateTime.now

    # Now, add four hours to that date.
    # This also sucks.
    today = today - Rational(4, 24)

    today = DateTime.parse(today.to_s.split('T')[0])

    File.open(log_file_path) do |file|
      file.each do |line|

        this_date = DateTime.parse(line.split(' ')[0])

        if this_date == today
          if line.include?("photo upload limit")
            count += 1
          end
        end

      end
    end

    report(:changing_lives_over_limit_errors => count)

  end
end