class ChangingLivesPostErrors < Scout::Plugin
  def build_report

    log_file_path = '/var/log/changing-lives.log'

    # First, decide if we're running for the first time or not.
    if not memory(:count)

      # Check the Scout memory for a count. If it's null, we're new!
      # Just remember the current count, 0, and do nothing else.
      remember :count => 0

    else

      # We are not running for the first time. Let's zero out the count.
      count = 0

      # Now, let's read the file for error lines and count them.
      File.open(log_file_path) do |file|
        file.each do |line|

          if line.include?("ERROR")
            count += 1
          end

        end
      end

      # If the current count of errors in the log is greater than the
      # remembered number of errors, WE HAVE NEW ERRORS and we should
      # alert Brian because he likes that sort of thing.
      if count > memory(:count)

        # Remember the current count, blowing away the old count.
        remember :count => count

        # Raise an alert. First bit is the subject, second is the body.
        $count = count
        alert('Errors in Changing Lives!', 'There have been #$count errors since the last report.')

      else

        # Otherwise, just remember the current count by looking up the
        # one in memory now and saving it.
        remember :count => count

      end

    end

  end
end